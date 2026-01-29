from sklearn.linear_model import LogisticRegression as logisticregression
from sklearn.neighbors import KNeighborsClassifier as knnclassifier
from sklearn.tree import DecisionTreeClassifier as decisiontreeclassifier
from sklearn.ensemble import RandomForestClassifier as randomforestclassifier
from sklearn.ensemble import GradientBoostingClassifier as gradientboostingclassifier
from sklearn.ensemble import AdaBoostClassifier as adaboostclassifier
from xgboost import XGBClassifier as xgboostclassifier
from sklearn.svm import SVC as supportvectorclassifer


class LogisticRegressionmodel:
    def __init__(self, **kwargs):
        self.model = logisticregression(**kwargs)
    
    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)


class KNeighborsClassifiermodel:
    def __init__(self, **kwargs):
        self.model = knnclassifier(**kwargs)

    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)

class DecisionTreeClassifiermodel:
    def __init__(self, **kwargs):
        self.model = decisiontreeclassifier(**kwargs)
    
    def fit(self,X,y):
        self.model.fit(X,y)

    def predict(self, X):
        self.model.predict(X)

class RandomForestClassifiermodel:
    def __init__(self, **kwargs):
        self.model = randomforestclassifier(**kwargs)
    
    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self, X):
        self.model.predict(X)

class GradientBoostingClassifiermodel:
    def __init__(self, **kwargs):
        self.model = gradientboostingclassifier(**kwargs)
    
    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self, X):
        self.model.predict(X)

class AdaBoostClassifiermodel:
    def __init__(self, **kwargs):
        self.model = adaboostclassifier(**kwargs)
    
    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self, X):
        self.model.predict(X)

class SVClassifiermodel:
    def __init__(self, **kwargs):
        self.model = supportvectorclassifer(**kwargs)
    
    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self, X):
        self.model.predict(X)

class XGBClassifiermodel:
    def __init__(self, **kwargs):
        self.model = xgboostclassifier(**kwargs)

    def fit (self, X,y):
        self.model.fit(X,y)

    def predict(self, X):
        self.model.fit(X)