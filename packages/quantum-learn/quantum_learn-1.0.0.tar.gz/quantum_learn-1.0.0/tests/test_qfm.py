import unittest
import numpy as np
import pandas as pd
from qlearn import QuantumFeatureMap

try:
    from qlearn.pennylane import QuantumFeatureMap as PennylaneQuantumFeatureMap
    HAS_PENNYLANE = True
except Exception:
    HAS_PENNYLANE = False

try:
    from qlearn.qiskit import QuantumFeatureMap as QiskitQuantumFeatureMap
    HAS_QISKIT = True
except Exception:
    HAS_QISKIT = False

def simple_qfm_dataset():
    # Create a small dataset with two features
    data = pd.DataFrame({
        "feature1": [0.1, 0.2, 0.3],
        "feature2": [0.4, 0.5, 0.6]
    })
    return data

class TestQuantumFeatureMap(unittest.TestCase):
    def setUp(self):
        self.qfm = QuantumFeatureMap()
        self.data = simple_qfm_dataset()

    def test_transform(self):
        # Test that transform returns a numpy array with the correct shape.
        # Here we specify qubits=2.
        transformed = self.qfm.transform(self.data, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame) # Check if the output is a pandas DataFrame

    def test_transform_no_data(self):
        # Test that providing None as data raises a ValueError.
        with self.assertRaises(ValueError):
            self.qfm.transform(None, qubits=2)


@unittest.skipUnless(HAS_PENNYLANE, "pennylane backend not available")
class TestPennylaneQuantumFeatureMap(unittest.TestCase):
    def setUp(self):
        self.qfm = PennylaneQuantumFeatureMap()
        self.data = simple_qfm_dataset()

    def test_transform(self):
        transformed = self.qfm.transform(self.data, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)


@unittest.skipUnless(HAS_QISKIT, "qiskit backend not available")
class TestQiskitQuantumFeatureMap(unittest.TestCase):
    def setUp(self):
        self.qfm = QiskitQuantumFeatureMap()
        self.data = simple_qfm_dataset()

    def test_transform(self):
        transformed = self.qfm.transform(self.data, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)

if __name__ == "__main__":
    unittest.main()
