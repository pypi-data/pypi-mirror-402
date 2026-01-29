from sklearn.cluster import KMeans
from sklearn.cluster import MeanShift
from sklearn.cluster import MiniBatchKMeans

from .qfm import QuantumFeatureMap
qfm = QuantumFeatureMap()

class HybridClustering:

    def predict(self, data, n_clusters=0, model=None, random_state=42):
        if model is None:
            if n_clusters == 0:
                model = MeanShift()
                if len(data) > 10000:
                    print('MeanShift is recommended for datasets with <10k samples, \n'
                    'clustering without a set number of clusters and >10k samples is not recommended.')
                
            
            else:
                if len(data) < 10000:
                    model = KMeans(n_clusters=n_clusters, random_state=random_state)
                else:
                    model = MiniBatchKMeans(n_clusters=n_clusters, random_state=random_state)


        return model.fit_predict(qfm.transform(data))
