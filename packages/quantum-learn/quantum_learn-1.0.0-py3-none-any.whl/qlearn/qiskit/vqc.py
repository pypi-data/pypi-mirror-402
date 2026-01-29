from qlearn.backends.base import VariationalQuantumCircuitBase


class VariationalQuantumCircuit(VariationalQuantumCircuitBase):
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
        raise NotImplementedError("Qiskit backend is not implemented yet.")

    def predict(self, features, n_qubits=None, device=None, diff_method="backprop"):
        raise NotImplementedError("Qiskit backend is not implemented yet.")
