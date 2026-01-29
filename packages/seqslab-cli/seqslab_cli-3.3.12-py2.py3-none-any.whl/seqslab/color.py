def color_handler(func):
    ColorDict = {"yellow": "\033[01;33m", "green": "\033[01;32m", "red": "\033[01;31m"}

    def inner_function(*args, **kwargs):
        kwargs.update(ColorDict)
        return func(*args, **kwargs)

    return inner_function
