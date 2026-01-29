import unittest
import numpy as np
import pandas as pd
from qlearn import HybridClustering

def simple_dataset():
    data = pd.DataFrame({
        "feature1": [0, 1, 0, 1, 2],
        "feature2": [0, 0, 1, 1, 2]
    })
    return data

class TestClustering(unittest.TestCase):
    def setUp(self):
        self.data = simple_dataset()
        self.clusterer = HybridClustering()

    def test_clustering(self):
        # Test that clustering returns an array of labels equal in length to the data.
        clusters = self.clusterer.predict(self.data, n_clusters=2)
        self.assertEqual(len(clusters), len(self.data))
        self.assertIsInstance(clusters, np.ndarray)

if __name__ == "__main__":
    unittest.main()
