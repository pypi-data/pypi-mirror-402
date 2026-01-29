import pandas as pd
import pennylane as qml
from pennylane import numpy as np

from qlearn.backends.base import VariationalQuantumCircuitBase


class VariationalQuantumCircuit(VariationalQuantumCircuitBase):
    def __init__(self):
        self.params = None
        self.ansatz = None

    def generator(self, features, params, n_qubits, device, ansatz=None):
        @qml.qnode(device, diff_method="backprop")
        def circuit(features, params):
            if ansatz is not None:
                return ansatz(features, params, n_qubits)
            # Default ansatz
            for i in range(n_qubits):
                qml.Rot(
                    features[i] * params[i][0],
                    features[i] * params[i][1],
                    features[i] * params[i][2],
                    wires=i,
                )
                if i < n_qubits - 1:
                    qml.CNOT(wires=[i, i + 1])
            return qml.state()

        return circuit(features, params)

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
        optimizer=qml.AdamOptimizer(stepsize=0.05),
    ):
        if features is None or labels is None:
            raise ValueError("Features and labels cannot be None.")

        if n_qubits is None:
            n_qubits = len(features.columns)

        if device is None:
            device = qml.device("default.qubit", wires=n_qubits)

        if params is None:
            params = np.random.randn(n_qubits, 3)

        self.ansatz = ansatz
        data = pd.concat([features, labels], axis=1)

        def fidelity_loss(output, target):
            state0 = qml.math.dm_from_state_vector(output)
            state1 = qml.math.dm_from_state_vector(target)
            error = 1 - qml.math.fidelity(state0, state1)
            return error

        def learn():
            params = np.random.randn(n_qubits, 3)
            print(params)
            for _ in range(epochs):
                costs = []
                for start_idx in range(0, len(data), batch_size):
                    end_idx = min(start_idx + batch_size, len(data))
                    batch_data = data.iloc[start_idx:end_idx]

                    def cost_function(params):
                        total_loss = 0
                        for _, row in batch_data.iterrows():
                            total_loss += fidelity_loss(
                                self.generator(
                                    [row[feature] for feature in features.columns],
                                    params,
                                    n_qubits,
                                    device,
                                    ansatz,
                                ),
                                [row[label] for label in labels.columns],
                            )
                        return qml.math.mean(total_loss / len(batch_data))

                    params, cost = optimizer.step_and_cost(cost_function, params)
                    costs.append(cost)
            return params

        self.params = learn()

    def predict(self, features, n_qubits=None, device=None, diff_method="backprop"):
        if n_qubits is None:
            n_qubits = len(features.columns)
        if device is None:
            device = qml.device("default.qubit", wires=n_qubits)
        predictions = []
        for _, row in features.iterrows():
            feat = [row[feature] for feature in features.columns]
            output = self.generator(feat, self.params, n_qubits, device, self.ansatz)
            predictions.append(output)
        return predictions
