from bakit.config import settings


def __getattr__(name):
    # This makes `from bakit.settings import MY_SETTING` to work
    return getattr(settings, name)
