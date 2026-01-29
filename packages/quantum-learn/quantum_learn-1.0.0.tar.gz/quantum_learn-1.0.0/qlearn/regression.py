from sklearn.linear_model import Lasso
from sklearn.linear_model import SGDRegressor

from .qfm import QuantumFeatureMap
qfm = QuantumFeatureMap()

class HybridRegression:
    def __init__(self):
        self.model = None

    def train(self, features, labels, model=None, random_state=42):
        if model is None:
            if len(features) < 100000:
                model = Lasso(random_state=random_state)
            
            else:
                model = SGDRegressor(random_state=random_state)

        model.fit(qfm.transform(features), labels)

        self.model = model

    # Write a predict  function for our model
    def predict(self, features):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        
        return self.model.predict(qfm.transform(features))