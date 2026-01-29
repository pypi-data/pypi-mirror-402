from sklearn.model_selection import train_test_split
from ..utils.logger import logger

class Splitter:
    """Handles data splitting for training and evaluation."""
    
    def __init__(self, test_size=0.2, random_state=42):
        self.test_size = test_size
        self.random_state = random_state

    def split(self, X, y):
        """Split data into train and test sets."""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )
        logger.info(f"Data split into train ({len(X_train)}) and test ({len(X_test)}) sets.")
        return X_train, X_test, y_train, y_test

