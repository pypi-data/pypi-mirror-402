import warnings

import pandas as pd
import pennylane as qml
from pennylane import numpy as np

from qlearn.backends.base import QuantumFeatureMapBase


class QuantumFeatureMap(QuantumFeatureMapBase):
    def default_feature_map(data, qubits):
        # Layer 1: Initial rotations
        for i in range(min(len(data), qubits)):
            qml.RY(data.iloc[i].item(), wires=i)
            qml.RX(data.iloc[i].item(), wires=i)

        # Superposition Layer: After initial rotations
        for i in range(qubits):
            qml.Hadamard(wires=i)

        # Layer 2: Controlled rotations for added non-linearity
        for i in range(1, min(len(data), qubits)):
            qml.CRY(data.iloc[i].item(), wires=[i - 1, i])
            qml.CRZ(data.iloc[i].item(), wires=[i - 1, i])

        # Layer 3: Reverse entanglement
        for i in range(qubits - 1, 0, -1):
            for j in range(i - 1, -1, -1):
                qml.CNOT(wires=[i, j])

        # Layer 4: More parameterized rotations
        for i in range(min(len(data), qubits)):
            qml.RX(data.iloc[i].item() * 0.8, wires=i)
            qml.RZ(data.iloc[i].item() * 1.2, wires=i)

        # Layer 6: Final rotations for classification resolution
        for i in range(min(len(data), qubits)):
            qml.RY(data.iloc[i].item(), wires=i)
            qml.RZ(data.iloc[i].item(), wires=i)

    def transform(self, data=None, feature_map=None, qubits=None, device=None):
        "Transforms classical data using a quantum feature map in Pennylane"

        if data is None:
            raise ValueError("Data cannot be None.")

        if qubits is None:
            qubits = len(data.columns)
            warnings.warn(
                "The number of qubits required is not specified, by default the number of columns in the data will be used."
            )

        if device is None:
            device = qml.device("default.qubit", wires=qubits)

        if feature_map is None:
            feature_map = QuantumFeatureMap.default_feature_map
            warnings.warn(
                "No feature map is specified, by default a general purpose feature map will be used. It is recommended to use a custom feature map fit for the data."
            )
        elif type(feature_map) == str:
            if feature_map == "default":
                feature_map = QuantumFeatureMap.default_feature_map
        elif callable(feature_map):
            pass
        else:
            raise ValueError(
                "Feature map must be a function or a string containing a valid feature map name."
            )

        @qml.qnode(device)
        def quantum_circuit(data):
            feature_map(data, qubits)
            return [qml.expval(qml.PauliZ(i)) for i in range(qubits)]

        transformed_data = []
        for _, row in data.iterrows():
            transformed_data.append(quantum_circuit(row))

        transformed_df = pd.DataFrame(
            transformed_data,
            index=data.index,
            columns=[f"Qubit_{i}" for i in range(qubits)],
        )
        return transformed_df
