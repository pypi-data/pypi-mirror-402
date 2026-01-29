import pandas as pd
from ..utils.logger import logger

class Cleaner:
    """Handles missing values and basic data cleaning."""
    
    def __init__(self, strategy="auto"):
        self.strategy = strategy
        self.fill_values = {}

    def fit(self, df):
        """Identify missing values and determine fill strategies."""
        for col in df.columns:
            if df[col].isnull().any():
                if df[col].dtype in ['int64', 'float64']:
                    self.fill_values[col] = df[col].median()
                else:
                    self.fill_values[col] = df[col].mode()[0] if not df[col].mode().empty else "missing"
        
        logger.info(f"Cleaner identified {len(self.fill_values)} columns with missing values.")
        return self

    def transform(self, df):
        """Apply cleaning strategies."""
        df_clean = df.copy()
        for col, val in self.fill_values.items():
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(val)
        
        return df_clean

    def fit_transform(self, df):
        return self.fit(df).transform(df)
