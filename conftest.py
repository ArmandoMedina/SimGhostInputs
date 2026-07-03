import importlib.util

if importlib.util.find_spec("nicegui.testing") is not None:
    pytest_plugins = ["nicegui.testing.user_plugin"]
