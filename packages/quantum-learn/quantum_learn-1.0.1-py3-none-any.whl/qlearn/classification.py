from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier

from .qfm import QuantumFeatureMap
qfm = QuantumFeatureMap()

class HybridClassification:
    def __init__(self):
        self.model = None

    def train(self, features, labels, model=None, random_state=42):

        if model is None:
            if len(features) < 100000:
                model = SVC(kernel="linear", random_state=random_state)
            
                # If not working
                ## If text data, use Naive Bayes
                ## else use KNeigbhborsClassifier

            else:
                model = SGDClassifier(random_state=random_state)

        model.fit(qfm.transform(features), labels)

        self.model = model


    def predict(self, features):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        return self.model.predict(qfm.transform(features))