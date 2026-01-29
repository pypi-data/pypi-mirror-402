def print_stream(response_iterator):
    """
    Helper to print streaming responses (future proofing).
    Currently, the Agent.run method is synchronous, but this allows expansion.
    """
    for chunk in response_iterator:
        print(chunk.text, end="", flush=True)