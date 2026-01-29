"""Formatting utilities for the {{plugin_name}} plugin."""


def format_greeting(name: str, formal: bool = False) -> str:
    """Format a greeting message.

    Args:
        name: The name to include in the greeting
        formal: Whether to use a formal greeting

    Returns:
        A formatted greeting message

    Examples:
        >>> format_greeting("John")
        'Hello, John! This is the {{plugin_name_short}} plugin.'
        >>> format_greeting("John", formal=True)
        'Greetings, Mr/Ms John. Welcome to the {{plugin_name_short}} plugin.'
    """
    if formal:
        return f"Greetings, Mr/Ms {name}. Welcome to the {{plugin_name_short}} plugin."
    else:
        return f"Hello, {name}! This is the {{plugin_name_short}} plugin."
