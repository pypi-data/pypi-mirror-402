from functools import wraps

__all__ = ["use_error_details"]


def use_error_details(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["params"] = kwargs.get("params", {})
        if "error_details" in kwargs:
            kwargs["params"]["error_details"] = kwargs["error_details"]
        return func(*args, **kwargs)

    return wrapper
