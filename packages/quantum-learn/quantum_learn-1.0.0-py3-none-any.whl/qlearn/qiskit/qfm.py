import inspect
import warnings

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from qlearn.backends.base import QuantumFeatureMapBase


class QuantumFeatureMap(QuantumFeatureMapBase):
    """
    Qiskit-only quantum feature map transformer using StatevectorEstimator.

    Feature map function signatures supported:
      - feature_map(row, qubits, qc): modifies an existing QuantumCircuit in-place
      - feature_map(row, qubits): returns a QuantumCircuit
    """

    @staticmethod
    def default_feature_map(data, qubits, qc):
        """
        Default Qiskit feature map (only circuit code, no backend/measurement).

        `data` is assumed to behave like a pandas Series/row.
        """

        def get_val(i):
            try:
                return float(data.iloc[i].item())
            except AttributeError:
                return float(data[i])

        n = min(len(data), qubits)

        # Layer 1: Initial rotations
        for i in range(n):
            val = get_val(i)
            qc.ry(val, i)
            qc.rx(val, i)

        # Superposition layer
        for i in range(qubits):
            qc.h(i)

        # Layer 2: Controlled rotations
        for i in range(1, n):
            val = get_val(i)
            qc.cry(val, i - 1, i)
            qc.crz(val, i - 1, i)

        # Layer 3: Reverse entanglement
        for i in range(qubits - 1, 0, -1):
            for j in range(i - 1, -1, -1):
                qc.cx(i, j)

        # Layer 4: More parameterized rotations
        for i in range(n):
            val = get_val(i)
            qc.rx(0.8 * val, i)
            qc.rz(1.2 * val, i)

        # Layer 6: Final rotations
        for i in range(n):
            val = get_val(i)
            qc.ry(val, i)
            qc.rz(val, i)

    def transform(
        self,
        data=None,
        feature_map=None,
        qubits=None,
        estimator=None,
    ):
        """
        Transforms classical data using a quantum feature map with Qiskit.

        Parameters
        ----------
        data : pandas.DataFrame
            Input classical data (rows are samples).
        feature_map : callable or str, optional
            - If callable:
                * (row, qubits, qc): modifies qc in-place with qc.* gates
                * (row, qubits): returns a QuantumCircuit
            - If "default": uses QuantumFeatureMap.default_feature_map.
            - If None: same as "default".
        qubits : int, optional
            Number of qubits; if None, uses number of columns in `data`.
        estimator : qiskit.primitives.StatevectorEstimator, optional
            Estimator used to compute ⟨Z_i⟩; if None, a new StatevectorEstimator is created.

        Returns
        -------
        pandas.DataFrame
            DataFrame of shape (n_samples, qubits) with ⟨Z_i⟩ expectation values.
        """

        if data is None:
            raise ValueError("Data cannot be None.")

        if qubits is None:
            qubits = len(data.columns)
            warnings.warn(
                "The number of qubits required is not specified; "
                "using the number of columns in the data."
            )

        if feature_map is None:
            feature_map = QuantumFeatureMap.default_feature_map
            warnings.warn(
                "No feature map is specified; using a general-purpose default. "
                "It is recommended to use a custom feature map fit for the data."
            )
        elif isinstance(feature_map, str):
            if feature_map == "default":
                feature_map = QuantumFeatureMap.default_feature_map
            else:
                raise ValueError(
                    'Unknown feature map name. Only "default" is recognized.'
                )
        elif callable(feature_map):
            pass
        else:
            raise ValueError(
                "Feature map must be a function or a string containing a valid feature map name."
            )

        if estimator is None:
            estimator = StatevectorEstimator()

        transformed_data = []

        observables = []
        for i in range(qubits):
            pauli_str = ["I"] * qubits
            pauli_str[qubits - 1 - i] = "Z"
            observables.append(SparsePauliOp("".join(pauli_str)))

        sig = inspect.signature(feature_map)
        n_params = len(sig.parameters)

        for _, row in data.iterrows():
            if n_params == 3:
                qc = QuantumCircuit(qubits)
                feature_map(row, qubits, qc)
            elif n_params == 2:
                qc = feature_map(row, qubits)
                if not isinstance(qc, QuantumCircuit):
                    raise TypeError(
                        "Qiskit feature_map with 2 parameters must return a QuantumCircuit."
                    )
            else:
                raise TypeError(
                    "For Qiskit, feature_map must take (data, qubits, qc) "
                    "or (data, qubits) and return a QuantumCircuit."
                )

            pub = (qc, observables)
            job = estimator.run([pub])
            result = job.result()[0]

            expvals = np.ravel(result.data.evs).tolist()
            transformed_data.append(expvals)

        transformed_df = pd.DataFrame(
            transformed_data,
            index=data.index,
            columns=[f"Qubit_{i}" for i in range(qubits)],
        )
        return transformed_df
