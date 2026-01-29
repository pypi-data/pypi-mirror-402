"""
QuantumDL: A framework for quantum machine learning that integrates latest research results
in quantum computing and deep learning.
"""

__version__ = '1.0.1'


from . import circuit
from . import gate
from . import ansatz
from . import qmath
from . import state
from . import layer
from . import optimizer
from . import utils
from . import photonic
from . import mbqc
from . import distributed
from . import qnn

# PhotonicCircuit is not defined in circuit.py
# Only QubitCircuit and DistributedQubitCircuit are available
from .circuit import QubitCircuit, DistributedQubitCircuit

# Only import existing classes from ansatz
from .ansatz import (
    QuantumConvolutionalNeuralNetwork,
    QuantumFourierTransform,
    QuantumPhaseEstimation,
    QuantumPhaseEstimationSingleQubit,
    RandomCircuitG3,
    ShorCircuit,
    ShorCircuitFor15
)

# Only import existing classes from gate
from .gate import (
    SingleGate,
    DoubleGate,
    TripleGate,
    ParametricSingleGate,
    ParametricDoubleGate,
    ArbitraryGate,
    PauliX,
    PauliY,
    PauliZ,
    Hadamard,
    SGate,
    SDaggerGate,
    TGate,
    TDaggerGate,
    Rx,
    Ry,
    Rz,
    ProjectionJ,
    CNOT,
    Swap,
    ImaginarySwap,
    Rxx,
    Ryy,
    Rzz,
    Rxy,
    ReconfigurableBeamSplitter,
    Toffoli,
    Fredkin,
    UAnyGate,
    LatentGate,
    HamiltonianGate,
    Reset,
    Barrier,
    WireCut,
    Move
)

# QuantumLayer is not defined in layer.py
# Using SingleLayer as base class instead
# from .layer import SingleLayer as QuantumLayer

# QuantumNeuralNetwork, HybridQuantumClassicalModel, QuantumAttentionLayer are not defined in qnn.py
# from .qnn import ...

# QuantumNaturalGradientOptimizer, QuantumAdamOptimizer, QuantumSGDOptimizer are not defined in optimizer.py
# from .optimizer import ...

# Only import existing functions from qmath
from .qmath import (
    amplitude_encoding,
    expectation,
    measure
)
# quantum_entropy and quantum_mutual_information are not defined in qmath.py

# setup_distributed and cleanup_distributed are not defined in distributed.py
# from .distributed import (
#     setup_distributed,
#     cleanup_distributed
# )
