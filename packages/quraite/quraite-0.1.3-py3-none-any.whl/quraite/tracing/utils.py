import re
from typing import Any

# Keys to skip (they're just OpenInference namespacing prefixes)
SKIP_KEYS = {"message", "tool_call", "tool"}


def unflatten_messages(attributes: dict[str, Any]) -> dict[str, Any]:
    """
    Unflatten llm.input_messages and llm.output_messages from dot notation
    to nested list structures.

    Args:
        attributes: Flattened span attributes dict

    Returns:
        New dict with unflattened input_messages and output_messages
    """
    result = {}
    input_messages: dict[int, dict] = {}
    output_messages: dict[int, dict] = {}

    # Patterns to match message attributes
    input_pattern = re.compile(r"^llm\.input_messages\.(\d+)\.(.+)$")
    output_pattern = re.compile(r"^llm\.output_messages\.(\d+)\.(.+)$")

    for key, value in attributes.items():
        # Check for input messages
        input_match = input_pattern.match(key)
        if input_match:
            idx = int(input_match.group(1))
            rest = input_match.group(2)
            if idx not in input_messages:
                input_messages[idx] = {}
            _set_nested_value(input_messages[idx], rest, value)
            continue

        # Check for output messages
        output_match = output_pattern.match(key)
        if output_match:
            idx = int(output_match.group(1))
            rest = output_match.group(2)
            if idx not in output_messages:
                output_messages[idx] = {}
            _set_nested_value(output_messages[idx], rest, value)
            continue

        # Keep other attributes as-is
        result[key] = value

    # Convert dicts to sorted lists
    if input_messages:
        result["llm.input_messages"] = _dict_to_list(input_messages)
    if output_messages:
        result["llm.output_messages"] = _dict_to_list(output_messages)

    return result


def _set_nested_value(d: dict, path: str, value: Any) -> None:
    """
    Set a nested value in a dict using dot notation path.
    Skips intermediate keys like 'message' and 'tool_call'.

    Handles paths like:
        - message.role -> role
        - message.content -> content
        - message.tool_calls.0.tool_call.function.name -> tool_calls[0].function.name
    """
    # Filter out the namespace prefixes
    parts = [p for p in path.split(".") if p not in SKIP_KEYS]
    current = d

    for i, part in enumerate(parts[:-1]):
        next_part = parts[i + 1]

        # Check if next part is an index (for arrays)
        if next_part.isdigit():
            if part not in current:
                current[part] = {}
            current = current[part]
        elif part.isdigit():
            # Current part is an index
            idx = int(part)
            if not isinstance(current, dict):
                current = {}
            if idx not in current:
                current[idx] = {}
            current = current[idx]
        else:
            if part not in current:
                current[part] = {}
            current = current[part]

    # Set the final value
    final_key = parts[-1]
    if final_key.isdigit():
        current[int(final_key)] = value
    else:
        current[final_key] = value


def _dict_to_list(d: dict[int, Any]) -> list:
    """Convert a dict with integer keys to a sorted list."""
    if not d:
        return []
    max_idx = max(d.keys())
    result = []
    for i in range(max_idx + 1):
        if i in d:
            item = d[i]
            # Recursively convert any nested dicts with int keys to lists
            result.append(_convert_nested_arrays(item))
        else:
            result.append(None)
    return result


def _convert_nested_arrays(obj: Any) -> Any:
    """Recursively convert dicts with integer keys to lists."""
    if isinstance(obj, dict):
        # Check if all keys are integers (should be a list)
        if obj and all(isinstance(k, int) for k in obj.keys()):
            return _dict_to_list(obj)
        # Otherwise process each value
        return {k: _convert_nested_arrays(v) for k, v in obj.items()}
    return obj


def unflatten_llm_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """
    Unflatten all LLM-related attributes (messages and tools).

    Args:
        attributes: Flattened span attributes dict

    Returns:
        New dict with unflattened messages and tools
    """
    result = unflatten_messages(attributes)

    return result


# Example usage
if __name__ == "__main__":
    import json

    # Example flattened attributes
    flattened = {
        "llm.input_messages.0.message.role": "system",
        "llm.input_messages.0.message.content": "You are helpful.",
        "llm.input_messages.1.message.role": "user",
        "llm.input_messages.1.message.content": "What is 2+2?",
        "llm.input_messages.2.message.role": "assistant",
        "llm.input_messages.2.message.tool_calls.0.tool_call.id": "call_123",
        "llm.input_messages.2.message.tool_calls.0.tool_call.function.name": "calculator",
        "llm.input_messages.2.message.tool_calls.0.tool_call.function.arguments": '{"a": 2, "b": 2}',
        "llm.input_messages.3.message.role": "tool",
        "llm.input_messages.3.message.tool_call_id": "call_123",
        "llm.input_messages.3.message.content": "4",
        "llm.output_messages.0.message.role": "assistant",
        "llm.output_messages.0.message.content": "The answer is 4.",
        "llm.model_name": "gpt-4",
        "llm.tools.0.tool.json_schema": '{"type": "function", "function": {"name": "calculator"}}',
        "openinference.span.kind": "LLM",
    }

    unflattened = unflatten_llm_attributes(flattened)
    print(json.dumps(unflattened, indent=2))
