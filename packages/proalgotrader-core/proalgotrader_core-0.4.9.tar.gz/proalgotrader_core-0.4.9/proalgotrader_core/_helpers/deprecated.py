import functools


def deprecated(message: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            raise Exception(f"Function '{func.__name__}' is deprecated: {message}")

        return wrapper

    return decorator
