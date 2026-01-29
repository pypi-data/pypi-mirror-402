from sklearn.preprocessing import StandardScaler as SkScalar
from ..utils.logger import logger

class Scaler:
    """Handles feature scaling."""
    
    def __init__(self):
        self.scaler = SkScalar()
        self.num_cols = []

    def fit(self, df):
        """Identify numerical columns and fit scaler."""
        self.num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if self.num_cols:
            self.scaler.fit(df[self.num_cols])
        
        logger.info(f"Scaler identified {len(self.num_cols)} numerical columns.")
        return self

    def transform(self, df):
        """Transform numerical columns."""
        df_scaled = df.copy()
        if self.num_cols:
            df_scaled[self.num_cols] = self.scaler.transform(df[self.num_cols])
        return df_scaled

    def fit_transform(self, df):
        return self.fit(df).transform(df)

