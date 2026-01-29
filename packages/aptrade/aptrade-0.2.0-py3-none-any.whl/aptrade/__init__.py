from aptrade.version import VERSION

__version__ = VERSION


def get_version():
    print(f"aptrade version: {__version__}")
    return __version__
