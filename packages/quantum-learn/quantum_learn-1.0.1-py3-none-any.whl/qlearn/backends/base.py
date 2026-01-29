from abc import ABC, abstractmethod


class QuantumFeatureMapBase(ABC):
    @abstractmethod
    def transform(self, data=None, feature_map=None, qubits=None, device=None):
        pass


class VariationalQuantumCircuitBase(ABC):
    @abstractmethod
    def train(
        self,
        features,
        labels,
        params=None,
        batch_size=32,
        epochs=1,
        n_qubits=None,
        device=None,
        ansatz=None,
        optimizer=None,
    ):
        pass

    @abstractmethod
    def predict(self, features, n_qubits=None, device=None, diff_method="backprop"):
        pass
