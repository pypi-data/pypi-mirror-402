from abc import ABC, abstractmethod
import os
import pickle
from datetime import datetime
from ..utils.logger import logger
from ..io.model_saver import ModelSaver
# Circular import concern if we import ModelLoader here, 
# so we might use it inside the method or rely on the high-level API.
class BaseModel(ABC):
    """Abstract Base Class for all evoMdl models."""

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__
        self.model = None
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "model_type": self.name,
            "version": "1.0.0"
        }

    @abstractmethod
    def fit(self, X, y, **kwargs):
        """Train the model."""
        pass

    @abstractmethod
    def predict(self, X, **kwargs):
        """Make predictions."""
        pass

    @abstractmethod
    def evaluate(self, X, y, **kwargs):
        """Evaluate the model."""
        pass

    def save(self, path):
        """Save the model using the ModelSaver utility."""
        ModelSaver.save(self, path)

    @classmethod
    def load(cls, path):
        """Load the model using the ModelLoader utility."""
        from ..io.model_loader import ModelLoader
        return ModelLoader.load(cls, path)
