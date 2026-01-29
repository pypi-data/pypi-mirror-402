from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class InputData:
    x: np.ndarray
    input_y: np.ndarray
    normalized_y: np.ndarray


@dataclass(frozen=True)
class ApproxResults:
    x: np.ndarray
    upper_y: np.ndarray
    bottom_y: np.ndarray
    

@dataclass(frozen=True)
class FuzzaproxResult:
    input_data: InputData
    forward: ApproxResults
    inverse: ApproxResults
