
class SuperWrapper:
    @classmethod
    def wrap(parent_class, method):
        def wrapper(self, *args, **kwargs):
            parent_method = getattr(parent_class, method.__name__)
            return parent_method(self, method, *args, **kwargs)
        wrapper.__name__ = method.__name__
        return wrapper
