from .auto_expiry import AutoExpiry

# Singleton pattern - Ensuring that only one instance of the class is created per given identifier
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        identifier = kwargs.get("identifier", "default")
        if cls not in cls._instances:
            cls._instances[cls] = {}
        if identifier not in cls._instances[cls]:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls][identifier] = instance
        return cls._instances[cls][identifier]


class AutoExpirySingletonMeta(SingletonMeta, type(AutoExpiry)):
    pass