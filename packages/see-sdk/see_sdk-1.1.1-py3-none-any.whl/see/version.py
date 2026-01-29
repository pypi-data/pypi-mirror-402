try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("see-sdk")
except ImportError:
    # Fallback for Python < 3.8
    try:
        from importlib_metadata import PackageNotFoundError, version  # type: ignore

        __version__ = version("see-sdk")
    except ImportError:
        __version__ = "unknown"
except PackageNotFoundError:
    # Package is not installed
    __version__ = "unknown"
