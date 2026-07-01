try:
    import nicegui.testing  # noqa: F401

    pytest_plugins = ["nicegui.testing"]
except ImportError:
    pytest_plugins = []
