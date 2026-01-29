import unittest
import numpy as np
import pandas as pd
from qlearn import VariationalQuantumCircuit

try:
    from qlearn.pennylane import VariationalQuantumCircuit as PennylaneVariationalQuantumCircuit
    HAS_PENNYLANE = True
except Exception:
    HAS_PENNYLANE = False

try:
    from qlearn.qiskit import VariationalQuantumCircuit as QiskitVariationalQuantumCircuit
    HAS_QISKIT = True
except Exception:
    HAS_QISKIT = False

def simple_quantum_dataset():
    # For a 2-qubit system, a valid state vector has 4 elements.
    # Here we encode:
    # 0 -> |00 = [1, 0, 0, 0]
    # 1 -> |11 = [0, 0, 0, 1]
    def encode(label):
        return np.array([1, 0, 0, 0]) if label == 0 else np.array([0, 0, 0, 1])
    
    data = pd.DataFrame({
        "feature1": [0, 1, 0, 1],
        "feature2": [0, 0, 1, 1],
        "label": [encode(l) for l in [0, 1, 1, 0]]
    })
    return data


class TestVariationalQuantumCircuit(unittest.TestCase):

    def setUp(self):
        # Setup simple quantum dataset
        data = simple_quantum_dataset()
        self.features = data[["feature1", "feature2"]]
        self.labels = data[["label"]]
        self.vqc = VariationalQuantumCircuit()

    def test_train(self):
        # Test if training works
        self.vqc.train(self.features, self.labels, epochs=2)
        self.assertIsNotNone(self.vqc.params)
        self.assertEqual(self.vqc.params.shape[0], len(self.features.columns))

    def test_predict(self):
        # Test if prediction works
        self.vqc.train(self.features, self.labels, epochs=2)
        predictions = self.vqc.predict(self.features)
        self.assertEqual(len(predictions), len(self.features))

    def test_invalid_features(self):
        # Test invalid input handling
        with self.assertRaises(ValueError):
            self.vqc.train(None, self.labels, epochs=2)


@unittest.skipUnless(HAS_PENNYLANE, "pennylane backend not available")
class TestPennylaneVariationalQuantumCircuit(unittest.TestCase):
    def setUp(self):
        data = simple_quantum_dataset()
        self.features = data[["feature1", "feature2"]]
        self.labels = data[["label"]]
        self.vqc = PennylaneVariationalQuantumCircuit()

    def test_train(self):
        self.vqc.train(self.features, self.labels, epochs=2)
        self.assertIsNotNone(self.vqc.params)
        self.assertEqual(self.vqc.params.shape[0], len(self.features.columns))

    def test_predict(self):
        self.vqc.train(self.features, self.labels, epochs=2)
        predictions = self.vqc.predict(self.features)
        self.assertEqual(len(predictions), len(self.features))


@unittest.skipUnless(HAS_QISKIT, "qiskit backend not available")
class TestQiskitVariationalQuantumCircuit(unittest.TestCase):
    def setUp(self):
        data = simple_quantum_dataset()
        self.features = data[["feature1", "feature2"]]
        self.labels = data[["label"]]
        self.vqc = QiskitVariationalQuantumCircuit()

    def test_train_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.vqc.train(self.features, self.labels, epochs=2)

    def test_predict_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.vqc.predict(self.features)


if __name__ == "__main__":
    unittest.main()

#python -m unittest discover -s tests
