import pandas as pd
from ..core.base_model import BaseModel
from ..core.automl import AutoMLEngine
from ..preprocessing.pipeline import Pipeline
from ..preprocessing.splitter import Splitter
from ..io.data_loader import DataLoader
from ..utils.logger import logger

class Classifier(BaseModel):
    """Enterprise-grade AutoML Classifier."""

    def __init__(self, **kwargs):
        super().__init__(name="Classifier")
        self.pipeline = Pipeline()
        self.engine = AutoMLEngine(task="classification")
        self.splitter = Splitter()

    def fit(self, data, target, **kwargs):
        """Standard fit method: handles data loading, preprocessing, and model selection."""
        if isinstance(data, str):
            data = DataLoader.load(data)
        
        self.target = target
        X = data.drop(columns=[target])
        y = data[target]

        self.metadata["target_col"] = target
        logger.info(f"Starting automated classification pipeline with target: {target}")
        
        # Preprocessing
        X_processed = self.pipeline.fit_transform(X)
        
        # Split
        X_train, X_val, y_train, y_val = self.splitter.split(X_processed, y)
        
        # AutoML Selection
        self.model = self.engine.select_best(X_train, y_train, X_val, y_val)
        
        # Refit on full data optional? For now just keep the best from split
        logger.info("Classification pipeline complete.")
        return self

    def predict(self, data, **kwargs):
        """Make predictions on new data. Automatically drops target column if present."""
        if isinstance(data, str):
            data = DataLoader.load(data)
        
        X = data.copy()
        if hasattr(self, 'target') and self.target in X.columns:
            X = X.drop(columns=[self.target])
        
        X_processed = self.pipeline.transform(X)
        return self.model.predict(X_processed)

    def evaluate(self, data, target, **kwargs):
        """Evaluate the model on a dataset."""
        if isinstance(data, str):
            data = DataLoader.load(data)
            
        X_processed = self.pipeline.transform(data.drop(columns=[target]))
        preds = self.model.predict(X_processed)
        # return accuracy_score(data[target], preds) ...
        pass

