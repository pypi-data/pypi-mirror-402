### batabyal
**batabyal** is a lightweight Python package that provides:
- **cleaning_module** for CSV data cleaning utilities
- **trainer_kit** for automatic best machine-learning model selection and training works on roc_auc score
It is designed for rapid experimentation, prototyping, and small-to-medium ML workflows where you want sensible defaults without repetitive boilerplate.

---

### Installation
```bash
pip install batabyal
```

### Importation
```python
from batabyal import trainer_kit as tk
from batabyal import cleaning_module as cm
```

### Usage
```python
tk.train(x, y, "numeric", "multiclass", 3) 
#structure: train(x, y, x_type:XType, y_type:YType, n_splits:int, random_state:int|None=42)
#XType = Literal["numeric", "one_hot", "mixed"]
#YType = Literal["binary", "multiclass"]

cm.clean_csv('filename.csv', numericData, charData, True) 
#structure: clean_csv(file, numericData, charData, Fill, dummies=None)
#If `Fill==True`, it fills NaN in numeric columns with its mean. 
#`dummies` are the list of values to replace with NaN before cleaning.
```

---

### 'trainer_kit' details
it uses:
- **StratifiedKFold** and **GridSearchCV** to find the best estimator
- `roc_auc_ovr_weighted` for scoring
it is limited to:
- LogisticRegression,
- DecisionTreeClassifier,
- RandomForestClassifier,
- GaussianNB,
- BernoulliNB 
use it when:
- you have **binary or multi-classed datasets** with target labels (i.e. only for ClassifierMixin)
don't use when:
- your dataset is single-classed
it assumes:
- your dataset is perfectly cleaned
- one hot encoded (if applicable)
- data is scaled (if applicable)
- column order is same for train and test data
it returns:
- the best trained model and its roc_auc score with the best hyperparameter tunning

### 'cleaning_module' details
only for `.csv` file cleaning
it returns the cleaned dataframe

---

*This package will help you to train supervised learning models quicker*