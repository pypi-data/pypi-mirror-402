import os
import platform
import re
import shutil
import stat
import subprocess
import threading
import time
from pathlib import Path
from urllib.request import urlopen

from quraite.logger import get_logger

# Cloudflare Tunnel download URLs
CLOUDFLARED_RELEASES_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download"
)
PLATFORMS = {
    "darwin_x86_64": f"{CLOUDFLARED_RELEASES_URL}/cloudflared-darwin-amd64",
    "darwin_arm64": f"{CLOUDFLARED_RELEASES_URL}/cloudflared-darwin-arm64",
    "windows_x86_64": f"{CLOUDFLARED_RELEASES_URL}/cloudflared-windows-amd64.exe",
    "linux_x86_64": f"{CLOUDFLARED_RELEASES_URL}/cloudflared-linux-amd64",
    "linux_arm64": f"{CLOUDFLARED_RELEASES_URL}/cloudflared-linux-arm64",
    "linux_arm": f"{CLOUDFLARED_RELEASES_URL}/cloudflared-linux-arm",
}

logger = get_logger(__name__)


class CloudflaredError(Exception):
    """Base exception for cloudflared operations."""


class CloudflaredTunnel:
    """Represents a Cloudflare Tunnel connection."""

    def __init__(self, public_url: str, process: subprocess.Popen):
        self.public_url = public_url
        self._process = process

    def disconnect(self):
        """Disconnect the tunnel."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()


def get_system() -> str:
    """Get the system platform identifier."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "darwin_arm64"
        return "darwin_x86_64"
    elif system == "windows":
        return "windows_x86_64"
    elif system == "linux":
        if machine in ("arm64", "aarch64"):
            return "linux_arm64"
        elif machine.startswith("arm"):
            return "linux_arm"
        return "linux_x86_64"
    else:
        raise CloudflaredError(f"Unsupported platform: {system} {machine}")


def get_cloudflared_path() -> Path:
    """Get the path where cloudflared binary should be stored."""
    user_home = Path.home()
    system = platform.system().lower()

    if system == "darwin":
        config_dir = user_home / "Library" / "Application Support" / "cloudflared"
    elif system == "windows":
        config_dir = user_home / "AppData" / "Local" / "cloudflared"
    else:
        config_dir = (
            Path(os.environ.get("XDG_CONFIG_HOME", user_home / ".config"))
            / "cloudflared"
        )

    config_dir.mkdir(parents=True, exist_ok=True)

    if system == "windows":
        return config_dir / "cloudflared.exe"
    return config_dir / "cloudflared"


def download_cloudflared(force: bool = False) -> Path:
    """
    Download cloudflared binary for the current platform.

    Args:
        force: If True, re-download even if binary exists

    Returns:
        Path to the cloudflared binary
    """
    # Check if cloudflared is already in PATH
    cloudflared_cmd = (
        "cloudflared.exe" if platform.system() == "windows" else "cloudflared"
    )
    if shutil.which(cloudflared_cmd) and not force:
        return Path(shutil.which(cloudflared_cmd))

    cloudflared_path = get_cloudflared_path()
    system_key = get_system()

    if cloudflared_path.exists() and not force:
        # Check if binary is executable
        if platform.system() != "windows":
            st = os.stat(cloudflared_path)
            os.chmod(cloudflared_path, st.st_mode | stat.S_IEXEC)
        return cloudflared_path

    if system_key not in PLATFORMS:
        raise CloudflaredError(f"Unsupported platform: {system_key}")

    download_url = PLATFORMS[system_key]
    logger.info("Downloading cloudflared from %s...", download_url)

    try:
        with urlopen(download_url, timeout=30) as response:
            with open(cloudflared_path, "wb") as f:
                f.write(response.read())

        # Make executable on Unix systems
        if platform.system() != "windows":
            st = os.stat(cloudflared_path)
            os.chmod(cloudflared_path, st.st_mode | stat.S_IEXEC)

        logger.info("Downloaded cloudflared to %s", cloudflared_path)
        return cloudflared_path

    except Exception as e:
        raise CloudflaredError(f"Failed to download cloudflared: {e}") from e


def connect(port: int, host: str = "localhost") -> CloudflaredTunnel:
    """
    Create a Cloudflare Tunnel connection to the specified port.

    Args:
        port: Local port to tunnel
        host: Local host (default: localhost)

    Returns:
        CloudflaredTunnel object with public_url attribute
    """
    cloudflared_path = download_cloudflared()

    # Start cloudflared tunnel
    cmd = [
        str(cloudflared_path),
        "tunnel",
        "--url",
        f"http://{host}:{port}",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Parse output to get public URL
    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    def read_output():
        nonlocal public_url
        try:
            for line in process.stdout:
                if not line:
                    continue
                line = line.strip()
                if line:
                    logger.debug("[cloudflared] %s", line)
                # Look for URL in the line
                match = url_pattern.search(line)
                if match:
                    public_url = match.group(0)
                    break
        except Exception as e:
            logger.error("[cloudflared] Error reading output: %s", e)

    # Start reading output in a separate thread
    output_thread = threading.Thread(target=read_output, daemon=True)
    output_thread.start()

    # Wait for URL to be available (max 30 seconds)
    timeout = 30
    start_time = time.time()
    while public_url is None and (time.time() - start_time) < timeout:
        if process.poll() is not None:
            raise CloudflaredError("cloudflared process exited unexpectedly")
        time.sleep(0.1)

    if public_url is None:
        process.terminate()
        raise CloudflaredError("Failed to get public URL from cloudflared")

    return CloudflaredTunnel(public_url=public_url, process=process)
