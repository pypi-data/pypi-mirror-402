import pandas as pd
import numpy as np
import os
from evomdl import Classifier, Regressor

def create_synthetic_data(task="classification"):
    np.random.seed(42)
    X = np.random.rand(100, 5)
    if task == "classification":
        y = (X[:, 0] + X[:, 1] > 1).astype(int)
    else:
        y = X[:, 0] * 10 + X[:, 1] * 5 + np.random.normal(0, 0.1, 100)
    
    df = pd.DataFrame(X, columns=[f"feat_{i}" for i in range(5)])
    df["target"] = y
    
    # Add some categorical and missing values
    df["cat_feat"] = np.random.choice(["A", "B", "C"], 100)
    df.loc[0:10, "feat_2"] = np.nan
    
    return df

def test_classifier_flow():
    print("\n--- Testing Classifier Flow ---")
    data = create_synthetic_data("classification")
    data.to_csv("train_class.csv", index=False)
    
    model = Classifier()
    model.fit("train_class.csv", target="target")
    
    preds = model.predict("train_class.csv")
    print(f"Predictions sample: {preds[:5]}")
    
    model.save("test_model.evo")
    print("Model saved.")
    
    loaded_model = Classifier.load("test_model.evo")
    loaded_preds = loaded_model.predict("train_class.csv")
    
    assert np.array_equal(preds, loaded_preds)
    print("Load verification successful!")

def test_regressor_flow():
    print("\n--- Testing Regressor Flow ---")
    data = create_synthetic_data("regression")
    data.to_csv("train_reg.csv", index=False)
    
    model = Regressor()
    model.fit("train_reg.csv", target="target")
    
    preds = model.predict("train_reg.csv")
    print(f"Predictions sample: {preds[:5]}")
    
    model.save("reg_model.evo")
    print("Model saved.")
    
    loaded_model = Regressor.load("reg_model.evo")
    loaded_preds = loaded_model.predict("train_reg.csv")
    
    assert np.allclose(preds, loaded_preds)
    print("Load verification successful!")

def cleanup():
    for f in ["train_class.csv", "train_reg.csv", "test_model.evo", "reg_model.evo"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    try:
        test_classifier_flow()
        test_regressor_flow()
        print("\nAll SDK verification tests passed!")
    finally:
        cleanup()

