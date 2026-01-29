from ..utils.logger import logger

class ModelRegistry:
    """Registry for keeping track of available models and their implementations."""
    
    _registry = {}

    @classmethod
    def register(cls, name):
        """Decorator to register a model class."""
        def wrapper(model_cls):
            cls._registry[name] = model_cls
            return model_cls
        return wrapper

    @classmethod
    def get_model(cls, name):
        """Retrieve a model class by name."""
        if name not in cls._registry:
            raise ValueError(f"Model '{name}' not found in registry. Available models: {list(cls._registry.keys())}")
        return cls._registry[name]

    @classmethod
    def list_models(cls):
        """List all registered models."""
        return list(cls._registry.keys())

registry = ModelRegistry()

