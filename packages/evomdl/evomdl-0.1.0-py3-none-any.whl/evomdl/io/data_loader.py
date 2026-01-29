import pandas as pd
import os
from ..utils.logger import logger

class DataLoader:
    """Handles data ingestion from various sources."""
    
    @staticmethod
    def load(source, **kwargs):
        """Load data from a file path or directory."""
        if isinstance(source, str):
            if source.endswith(".csv"):
                logger.info(f"Loading CSV from {source}")
                return pd.read_csv(source, **kwargs)
            elif source.endswith(".parquet"):
                logger.info(f"Loading Parquet from {source}")
                return pd.read_parquet(source, **kwargs)
            elif os.path.isdir(source):
                logger.info(f"Connecting to directory: {source}")
                return source # For image/dl tasks
        
        raise ValueError(f"Unsupported data source: {source}")

