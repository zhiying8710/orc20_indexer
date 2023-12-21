registered_handlers = {}


def register_handler(key):
    """
    Register a handler function for a given key.

    Args:
        key (str): The key to associate with the handler function.

    Returns:
        function: The decorator function.

    """

    def decorator(func):
        registered_handlers[key] = func
        return func

    return decorator
