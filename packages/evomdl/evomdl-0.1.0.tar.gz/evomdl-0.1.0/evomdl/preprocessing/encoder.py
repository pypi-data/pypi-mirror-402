import pandas as pd
from sklearn.preprocessing import LabelEncoder
from ..utils.logger import logger

class Encoder:
    """Handles categorical encoding."""
    
    def __init__(self):
        self.encoders = {}
        self.cat_cols = []

    def fit(self, df):
        """Identify categorical columns and fit encoders."""
        self.cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in self.cat_cols:
            le = LabelEncoder()
            le.fit(df[col].astype(str))
            self.encoders[col] = le
        
        logger.info(f"Encoder identified {len(self.cat_cols)} categorical columns.")
        return self

    def transform(self, df):
        """Transform categorical columns."""
        df_encoded = df.copy()
        for col in self.cat_cols:
            if col in df_encoded.columns:
                # Handle unseen labels by mapping them to the most frequent or a default
                df_encoded[col] = df_encoded[col].astype(str).map(
                    lambda x: self.encoders[col].transform([x])[0] if x in self.encoders[col].classes_ else -1
                )
        return df_encoded

    def fit_transform(self, df):
        return self.fit(df).transform(df)
