import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, r2_score
from ..utils.logger import logger

class AutoMLEngine:
    """Core engine for automatic model selection and tuning."""
    
    def __init__(self, task="classification", models=None):
        self.task = task
        self.models_to_try = models or self._get_default_models()
        self.best_model = None
        self.best_score = -float('inf')

    def _get_default_models(self):
        if self.task == "classification":
            return {
                "xgboost": XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
                "random_forest": RandomForestClassifier(),
                "logistic_regression": LogisticRegression(max_iter=1000)
            }
        else:
            return {
                "xgboost": XGBRegressor(),
                "random_forest": RandomForestRegressor(),
                "ridge": Ridge()
            }

    def select_best(self, X_train, y_train, X_val, y_val, tune=True):
        """Train multiple models and select the best one based on performance."""
        logger.info(f"Starting model selection for {self.task} task...")
        
        for name, model in self.models_to_try.items():
            logger.info(f"Evaluating {name}...")
            try:
                # Basic training to compare
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                
                if self.task == "classification":
                    score = accuracy_score(y_val, preds)
                else:
                    score = r2_score(y_val, preds)
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_model = model
                    self.best_model_name = name
            except Exception as e:
                logger.error(f"Failed to train {name}: {str(e)}")
        
        if tune and self.best_model_name in ["xgboost", "random_forest"]:
            logger.info(f"Starting hyperparameter tuning for {self.best_model_name}...")
            self.best_model = self._tune_model(self.best_model_name, X_train, y_train, X_val, y_val)
            
        logger.info(f"Selected {self.best_model_name} as the best model with score {self.best_score:.4f}")
        return self.best_model

    def _tune_model(self, name, X_train, y_train, X_val, y_val):
        """Simple Optuna-based tuning."""
        import optuna
        
        def objective(trial):
            if name == "xgboost":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3)
                }
                model = XGBClassifier(**params) if self.task == "classification" else XGBRegressor(**params)
            else: # random_forest
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                    'max_depth': trial.suggest_int('max_depth', 5, 20)
                }
                model = RandomForestClassifier(**params) if self.task == "classification" else RandomForestRegressor(**params)
            
            model.fit(X_train, y_train)
            preds = model.predict(X_val)
            return accuracy_score(y_val, preds) if self.task == "classification" else r2_score(y_val, preds)

        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=5) # Small trials for speed
        
        logger.info(f"Best params found: {study.best_params}")
        
        # Refit best
        if name == "xgboost":
            best_model = XGBClassifier(**study.best_params) if self.task == "classification" else XGBRegressor(**study.best_params)
        else:
            best_model = RandomForestClassifier(**study.best_params) if self.task == "classification" else RandomForestRegressor(**study.best_params)
            
        best_model.fit(X_train, y_train)
        return best_model


