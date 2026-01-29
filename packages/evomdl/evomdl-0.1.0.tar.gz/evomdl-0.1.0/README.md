# evoMdl — Enterprise-Grade Vision

**A Plug-and-Play AutoML + AutoDL SDK**  
Where users don’t need ML knowledge at all.

## Quick Start
```python
from evomdl import Classifier

model = Classifier()
model.fit("data.csv", target="label")
preds = model.predict("new_data.csv")
model.save("model.evo")
```

## Features
- **Auto Preprocessing**: Cleaning, encoding, scaling.
- **Auto Model Selection**: Chooses between XGBoost, Random Forest, etc.
- **Auto DL**: Built-in support for Image and NLP tasks.
- **Enterprise Ready**: Logging, versioning, and reproducibility.
