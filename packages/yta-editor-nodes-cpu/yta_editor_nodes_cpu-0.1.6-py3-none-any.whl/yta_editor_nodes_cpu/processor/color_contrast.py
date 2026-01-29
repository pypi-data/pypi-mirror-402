from yta_editor_nodes_cpu.processor.abstract import _NodeProcessorCPU, _NodeProcessorCoreCPU
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class ColorContrastNodeProcessorCPU(_NodeProcessorCPU):
    """
    The node to modify the color contrast of an input
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
            node_processor = _ColorContrastNodeProcessorCoreCPU()
        )

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        factor: float = 1.5
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
    
class _ColorContrastNodeProcessorCoreCPU(_NodeProcessorCoreCPU):
    """
    *For internal use only*
    
    Node processor to modify the color contrast of the
    input.

    Depending on the factor:
    - `factor>1.0` = More contrast
    - `factor==1.0` = Same contrast
    - `factor<1.0` = Less contrast

    TODO: Improve this, its just temporary
    """

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        factor: float,
        # TODO: Should I remove **kwargs (?)
        **kwargs
    ):
        # Ensure float32 [0, 1]
        source = TextureUtils.numpy_to_float32(input)

        # We do this to be the same as in GPU but it
        # should be calculated... and also for the GPU
        mean = np.array([0.5, 0.5, 0.5, 0.5], dtype = np.float32)

        # mean = input.mean(
        #     axis = (0, 1),
        #     keepdims = True
        # )
        """
        factor > 1 -> More contrast
        factor < 1 -> Less contrast
        """
        out = (source - mean) * factor + mean
        out = np.clip(out, 0, 1)

        return out