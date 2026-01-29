import unittest
import numpy as np
import pandas as pd
from qlearn import QuantumFeatureMap
import warnings

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

    def test_transform_qubits_default_warns(self):
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            transformed = self.qfm.transform(self.data)
        self.assertIsInstance(transformed, pd.DataFrame)
        self.assertTrue(any("number of qubits" in str(w.message).lower() for w in warns))

    def test_transform_invalid_feature_map_name(self):
        with self.assertRaises(ValueError):
            self.qfm.transform(self.data, feature_map="nope", qubits=2)


@unittest.skipUnless(HAS_PENNYLANE, "pennylane backend not available")
class TestPennylaneQuantumFeatureMap(unittest.TestCase):
    def setUp(self):
        self.qfm = PennylaneQuantumFeatureMap()
        self.data = simple_qfm_dataset()

    def test_transform(self):
        transformed = self.qfm.transform(self.data, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)

    def test_default_feature_map_callable(self):
        transformed = self.qfm.transform(self.data, feature_map=self.qfm.default_feature_map, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)


@unittest.skipUnless(HAS_QISKIT, "qiskit backend not available")
class TestQiskitQuantumFeatureMap(unittest.TestCase):
    def setUp(self):
        self.qfm = QiskitQuantumFeatureMap()
        self.data = simple_qfm_dataset()

    def test_transform(self):
        transformed = self.qfm.transform(self.data, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)

    def test_feature_map_sets_qc_attribute(self):
        from qiskit import QuantumCircuit

        def feature_map(row, qubits):
            qc = QuantumCircuit(qubits)
            qc.h(0)
            feature_map.qc = qc

        transformed = self.qfm.transform(self.data, feature_map=feature_map, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)

    def test_feature_map_returns_qc(self):
        from qiskit import QuantumCircuit

        def feature_map(row, qubits):
            qc = QuantumCircuit(qubits)
            qc.h(0)
            return qc

        transformed = self.qfm.transform(self.data, feature_map=feature_map, qubits=2)
        self.assertIsInstance(transformed, pd.DataFrame)

    def test_feature_map_wrong_signature(self):
        def feature_map(row):
            return row

        with self.assertRaises(TypeError):
            self.qfm.transform(self.data, feature_map=feature_map, qubits=2)

    def test_feature_map_invalid_return(self):
        def feature_map(row, qubits):
            return None

        with self.assertRaises(TypeError):
            self.qfm.transform(self.data, feature_map=feature_map, qubits=2)

if __name__ == "__main__":
    unittest.main()
