from sklearn.linear_model import LinearRegression as linearregression
from sklearn.neighbors import KNeighborsRegressor as knnregressor
from sklearn.tree import DecisionTreeRegressor as decisiontreeregressor
from sklearn.ensemble import RandomForestRegressor as randomforestregressor
from sklearn.ensemble import GradientBoostingRegressor as gradientboostingregressor
from sklearn.ensemble import AdaBoostRegressor as adaboostregressor
from xgboost import XGBRegressor as xgboostregressor
from sklearn.svm import SVR as supportvectorregressor
from sklearn.linear_model import ElasticNet as elasticnetregressor



class LinearRegressionmodel:
    def __init__(self, **kwargs):
        self.model = linearregression(**kwargs)
    
    def fit(self, X,y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)


class KNNRegressionmodel:
    def __init__(self, **kwargs):
        self.model = knnregressor(**kwargs)
    
    def fit(self, X, y):
        self.model.fit(X,y)
    
    def predict(self, X):
        self.model.predict(X)

class DecisionTreeRegressionmodel:
    def __init__(self, **kwargs):
        self.model = decisiontreeregressor(**kwargs)
    
    def fit(self,X,y):
        self.model.fit(X,y)
    
    def predict(self, X):
        self.model.predict(X)

class RandomForestRegressionmodel:
    def __init__(self, **kwargs):
        self.model = randomforestregressor(**kwargs)

    def fit(self, X, y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)

class GradientBoostingRegressionmodel:
    def __init__(self, **kwargs):
        self.model = randomforestregressor(**kwargs)
    
    def fit(self, X, y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)
    
class AdaBoostRegressionmodel:
    def __init__(self, **kwargs):
        self.model = adaboostregressor(**kwargs)
    
    def fit(self, X, y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)

class XGBoostRegressionmodel:
    def __init__(self, **kwargs):
        self.model = xgboostregressor(**kwargs)
    
    def fit(self, X, y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)

class ElasticNetRegressionmodel:
    def __init__(self, **kwargs):
        self.model = elasticnetregressor(**kwargs)
    
    def fit(self, X, y):
        self.model.fit(X,y)
    
    def predict(self,X):
        self.model.predict(X)