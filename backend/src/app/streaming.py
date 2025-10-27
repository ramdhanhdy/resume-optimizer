from typing import Any, Dict, Tuple


def consume_stream(response_container, stream) -> Tuple[str, Dict[str, Any]]:
    """Consume a streaming generator into a UI container and capture metadata.

    Args:
        response_container: A Streamlit placeholder (e.g., st.empty()) used to render streaming text
        stream: A generator yielding text chunks and returning metadata via StopIteration.value

    Returns:
        A tuple of (full_text, metadata_dict)
    """
    full_response: str = ""
    metadata: Dict[str, Any] = {}

    try:
        while True:
            chunk = next(stream)
            full_response += chunk
            # Render with a blinking cursor effect
            response_container.markdown(full_response + "▌")
    except StopIteration as e:
        metadata = e.value if e.value else {}

    # Final render without the cursor
    response_container.markdown(full_response)
    return full_response, metadata
