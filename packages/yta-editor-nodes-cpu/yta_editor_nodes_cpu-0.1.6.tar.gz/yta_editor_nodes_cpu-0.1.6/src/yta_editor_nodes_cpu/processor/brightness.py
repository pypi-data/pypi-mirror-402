from yta_editor_nodes_cpu.processor.abstract import _NodeProcessorCPU, _NodeProcessorCoreCPU
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class BrightnessNodeProcessorCPU(_NodeProcessorCPU):
    """
    The node to modify the brightness of an input
    by using the CPU.

    This class can be instantiated many different
    times with different parameters, but will always
    call the same `Singleton` node processor instance
    to process the `input`.
    """
    
    def __init__(
        self
    ):
        super().__init__(
            node_processor = _BrightnessNodeProcessorCoreCPU()
        )

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        factor: float = 1.0
    ) -> np.ndarray:
        """
        Process the `input` provided by using the node
        processor instance associated to this node and
        return the output.
        """
        return self.node_processor.process(
            input = input,
            output_size = output_size,
            factor = factor
        )
    
class _BrightnessNodeProcessorCoreCPU(_NodeProcessorCoreCPU):
    """
    *For internal use only*

    *Singleton class*

    Node processor to modify the brightness of the
    input by multiplying it by a factor.

    Depending on the factor:
    - `factor>1.0` = Lighter
    - `factor==1.0` = Same brightness
    - `factor<1.0` = Darker
    """

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        factor: float,
        # TODO: Should I remove **kwargs (?)
        **kwargs
    ):
        """
        The `input` must be `float32` and the output will
        be also `float32`.
        """
        # Ensure float32 [0, 1]
        source = TextureUtils.numpy_to_float32(input)

        # Copy to avoid mutating upstream buffers
        output = source.copy()

        # Apply brightness (RGB only)
        output[..., :3] *= factor

        # Clamp
        output = np.clip(output, 0.0, 1.0)

        return output