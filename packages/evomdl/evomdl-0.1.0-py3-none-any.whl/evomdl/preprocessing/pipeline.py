import pandas as pd
from .cleaner import Cleaner
from .encoder import Encoder
from .scaler import Scaler
from ..utils.logger import logger

class Pipeline:
    """Orchestrates the preprocessing flow."""
    
    def __init__(self):
        self.cleaner = Cleaner()
        self.encoder = Encoder()
        self.scaler = Scaler()
        self._fitted = False

    def fit_transform(self, X):
        """Fit all components and transform data."""
        X = self.cleaner.fit_transform(X)
        X = self.encoder.fit_transform(X)
        X = self.scaler.fit_transform(X)
        self._fitted = True
        return X

    def transform(self, X):
        """Apply fitted transformations to data."""
        if not self._fitted:
            raise ValueError("Pipeline must be fitted before transform.")
        
        X = self.cleaner.transform(X)
        X = self.encoder.transform(X)
        X = self.scaler.transform(X)
        return X

    def save_state(self):
        """Return the state of the pipeline for persistence."""
        return {
            "cleaner": self.cleaner,
            "encoder": self.encoder,
            "scaler": self.scaler,
            "fitted": self._fitted
        }

    def load_state(self, state):
        """Restore the state of the pipeline."""
        self.cleaner = state["cleaner"]
        self.encoder = state["encoder"]
        self.scaler = state["scaler"]
        self._fitted = state["fitted"]

