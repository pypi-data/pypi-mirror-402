import pickle
from ..utils.logger import logger

class ModelSaver:
    """Utility for saving models and associated metadata."""
    
    @staticmethod
    def save(model_instance, path):
        """Save a model instance to the specified path."""
        if not path.endswith(".evo"):
            path += ".evo"
            
        # The model_instance is expected to have a 'model', 'metadata', and 'pipeline'
        data = {
            "model": model_instance.model,
            "metadata": model_instance.metadata,
            "pipeline_state": model_instance.pipeline.save_state() if hasattr(model_instance, 'pipeline') else None
        }
        
        with open(path, "wb") as f:
            pickle.dump(data, f)
            
        logger.info(f"Successfully saved {model_instance.name} to {path}")

