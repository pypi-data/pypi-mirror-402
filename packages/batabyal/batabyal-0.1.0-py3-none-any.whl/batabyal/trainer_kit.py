from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB, BernoulliNB
import numpy as np
from typing import Literal
from sklearn.base import ClassifierMixin

XType = Literal["numeric", "one_hot", "mixed"]
YType = Literal["binary", "multiclass"]

def train(x, y, x_type:XType, y_type:YType, n_splits:int, random_state:int|None=42) -> tuple[ClassifierMixin, float] :
    
    """
    Automatically trains multiple classifiers and selects the best based on ROC-AUC score.

    Parameters:
    ----------
    x : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Target vector.
    x_type : XType
        Type of input features: "numeric", "one_hot", or "mixed".
    y_type : YType
        Type of target: "binary" or "multiclass".
    n_splits : int
        Number of splits for StratifiedKFold cross-validation. Must be >= 2.
    random_state : Optional[int], default=42
        Random seed for reproducibility.

    Returns:
    -------
    Tuple[ClassifierMixin, float]
        Best trained model and its cross-validated score.
    """

    score='roc_auc_ovr_weighted'

    if (n_splits<2 or type(n_splits)!=int):
        raise ValueError ('n_splits must be integer and greater than 1')
    else:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    def lr_model(get_model=False) :
        param = {
                'C':[0.01, 0.1, 1, 10, 100],
                'class_weight':[None, 'balanced'],
                'solver':['lbfgs','newton-cg', 'saga'],
                'max_iter': [100000]
        }
        grid = GridSearchCV(LogisticRegression(), param, cv=cv, scoring=score, return_train_score=True, n_jobs=-1)
        grid.fit(x,y)
        if get_model :
            model = grid.best_estimator_
            return model, grid.best_score_
        return grid.best_score_

    def dt_model(get_model=False) :
        param = {
                'ccp_alpha':[0.0, 0.001],
                'class_weight':[None, 'balanced']
        }
        grid = GridSearchCV(DecisionTreeClassifier(), param, cv=cv, scoring=score, return_train_score=True, n_jobs=-1)
        grid.fit(x,y)
        if get_model :
            model = grid.best_estimator_
            return model, grid.best_score_
        return grid.best_score_

    def rf_model(get_model=False) :
        param = {
                'n_estimators':[int(len(y)/5), int(len(y)/3.33), int(len(y)/2.5)],
                'ccp_alpha':[0.0, 0.001],
                'class_weight':[None, 'balanced'],
                'max_features':[None]
        }
        grid = GridSearchCV(RandomForestClassifier(), param, cv=cv, scoring=score, return_train_score=True, n_jobs=-1)
        grid.fit(x, y)
        if get_model :
            model = grid.best_estimator_
            return model, grid.best_score_
        return grid.best_score_

    def GaussianNB_model(get_model=False) :
        grid = GridSearchCV(GaussianNB(), param_grid={}, cv=cv, scoring=score, return_train_score=True, n_jobs=-1)
        grid.fit(x,y)
        if get_model :
            model = grid.best_estimator_
            return model, grid.best_score_
        return grid.best_score_

    def BernoulliNB_model(get_model=False) :
        param = {'alpha':[0.001,0.01,0.1,1]}
        grid = GridSearchCV(BernoulliNB(), param, cv=cv, scoring=score, return_train_score=True, n_jobs=-1)
        grid.fit(x,y)
        if get_model :
            model = grid.best_estimator_
            return model, grid.best_score_
        return grid.best_score_
	
    def autofit(i) :
        if (i==0) :
            m, v = lr_model(get_model=True)
        elif (i==1) :
            m, v = dt_model(get_model=True)
        elif (i==2) :
            m, v = rf_model(get_model=True)
        elif (i==3) :
            m, v = GaussianNB_model(get_model=True)
        elif (i==4) :
            m, v = BernoulliNB_model(get_model=True)
        return m, v
	
    array = np.array([lr_model(), dt_model(), rf_model(), GaussianNB_model(), BernoulliNB_model()])

    if (x_type=="numeric" and y_type=="binary") :
        index = np.argmax(array[:4])
    elif (x_type=="one_hot" and y_type=="binary") :
        index = np.argmax(array[[0,1,2,4]])
        if (index==3) :
            index = 4
    elif(x_type=="mixed" and y_type=="binary") :
        index = np.argmax(array[:3])
    elif(x_type=="numeric" and y_type=="multiclass") :
        index = np.argmax(array[1:4])
        index +=1
    elif((x_type=="one_hot" or x_type=="mixed") and y_type=="multiclass") :
        index = np.argmax(array[1:3])
        index +=1
    else :
        raise ValueError('x_type can only accept "numeric", "one_hot", "mixed" and y_type can only accept "binary", "multiclass" values')

    m_final, v_final = autofit(index)
    return m_final, v_final