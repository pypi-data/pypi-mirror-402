import unittest
import numpy as np
import pandas as pd
from qlearn import HybridClassification

def simple_quantum_dataset():
    # For a 2-qubit system, a valid state vector has 4 elements.
    def encode(label):
        return np.array([1, 0, 0, 0]) if label == 0 else np.array([0, 0, 0, 1])
    data = pd.DataFrame({
        "feature1": [0, 1, 0, 1],
        "feature2": [0, 0, 1, 1],
        "label": [0, 1, 1, 0]
    })
    return data

class TestClassification(unittest.TestCase):
    def setUp(self):
        data = simple_quantum_dataset()
        self.features = data[["feature1", "feature2"]]
        self.labels = data[["label"]]
        self.clf = HybridClassification()

    def test_train_and_predict(self):
        # Test that after training, the model is set and predictions have the right length.
        self.clf.train(self.features, self.labels)
        self.assertIsNotNone(self.clf.model)
        predictions = self.clf.predict(self.features)
        self.assertEqual(len(predictions), len(self.features))

    def test_predict_without_training(self):
        # Expect a ValueError if predict is called without training.
        with self.assertRaises(ValueError):
            self.clf.predict(self.features)

    def test_custom_model(self):
        from sklearn.svm import SVC
        model = SVC(kernel="linear", random_state=123)
        self.clf.train(self.features, self.labels, model=model)
        self.assertIs(self.clf.model, model)

if __name__ == "__main__":
    unittest.main()
