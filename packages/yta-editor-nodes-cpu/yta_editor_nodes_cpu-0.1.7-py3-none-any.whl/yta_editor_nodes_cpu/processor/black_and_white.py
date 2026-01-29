from yta_editor_nodes_cpu.processor.abstract import _NodeProcessorCPU, _NodeProcessorCoreCPU
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class BlackAndWhiteNodeProcessorCPU(_NodeProcessorCPU):
    """
    The node to modify the input to become black and
    white only.

    This class can be instantiated many different
    times with different parameters, but will always
    call the same `Singleton` node processor instance
    to process the `input`.
    """
    
    def __init__(
        self
    ):
        super().__init__(
            node_processor = _BlackAndWhiteNodeProcessorCoreCPU()
        )

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        # TODO: Should we set the 'factor' here to be able
        # to modify it if it is different than None (?)
        # TODO: Should I remove **kwargs (?)
        **kwargs
    ) -> np.ndarray:
        """
        Process the `input` provided by using the node
        processor instance associated to this node and
        return the output.
        """
        return self.node_processor.process(
            input = input,
            output_size = output_size,
            **kwargs
        )
    
class _BlackAndWhiteNodeProcessorCoreCPU(_NodeProcessorCoreCPU):
    """
    *For internal use only*
    
    Node processor that modifies the input to become a
    black and white output.

    TODO: Improve this, its just temporary
    """

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        **kwargs
    ) -> np.ndarray:
        """
        The `input` must be `float32` and the output will
        be also `float32`.
        """
        # Ensure float32 [0, 1]
        source = TextureUtils.numpy_to_float32(input)

        # Standard luminance conversion Rec.709
        gray = 0.2126 * source[..., 0] + 0.7152 * source[..., 1] + 0.0722 * source[..., 2]
        gray = np.clip(gray, 0, 1)

        return np.dstack(
            [gray, gray, gray, input[..., 3]]
            if input.shape[-1] == 4 else
            [gray, gray, gray]
        )
    
