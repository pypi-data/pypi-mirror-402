import pickle
from ..utils.logger import logger

class ModelLoader:
    """Utility for loading models and restoring their state."""
    
    @staticmethod
    def load(model_class, path):
        """Load a model and restore its state into a new instance of model_class."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            
        instance = model_class()
        instance.model = data["model"]
        instance.metadata = data["metadata"]
        
        if "target_col" in instance.metadata:
            instance.target = instance.metadata["target_col"]
        
        if data.get("pipeline_state") and hasattr(instance, 'pipeline'):
            instance.pipeline.load_state(data["pipeline_state"])
            
        logger.info(f"Successfully loaded model from {path}")
        return instance

