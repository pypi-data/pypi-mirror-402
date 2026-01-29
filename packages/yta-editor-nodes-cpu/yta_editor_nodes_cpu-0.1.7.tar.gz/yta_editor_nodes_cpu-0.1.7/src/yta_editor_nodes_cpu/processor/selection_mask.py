from yta_editor_nodes_cpu.processor.abstract import _NodeProcessorCPU, _NodeProcessorCoreCPU
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class SelectionMaskNodeProcessorCPU(_NodeProcessorCPU):
    """
    The node to select the content by using a mask
    to determine if the pixel must be applied or
    not.

    This class can be instantiated many different
    times with different parameters, but will always
    call the same `Singleton` node processor instance
    to process the `input`.
    """
    
    def __init__(
        self
    ):
        super().__init__(
            node_processor = _SelectionMaskProcessorCoreCPU()
        )

    def process(
        self,
        original_input: np.ndarray,
        processed_input: np.ndarray,
        selection_mask_input: np.ndarray,
        output_size: Union[tuple[int, int], None]
    ) -> np.ndarray:
        """
        Process the `input` provided by using the node
        processor instance associated to this node and
        return the output.
        """
        return self.node_processor.process(
            original_input = original_input,
            processed_input = processed_input,
            selection_mask_input = selection_mask_input,
            output_size = output_size
        )

class _SelectionMaskProcessorCoreCPU(_NodeProcessorCoreCPU):
    """
    *For internal use only*
    
    Class to use a mask selection (from which we will
    determine if the pixel must be applied or not) to
    apply the `processed_input` on the `original_input`.
    """

    def process(
        self,
        # TODO: What about the type (?)
        original_input: np.ndarray,
        processed_input: np.ndarray,
        selection_mask_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        # TODO: Should I remove **kwargs (?)
        **kwargs
    ):
        """
        Apply the `selection_mask` provided to the also
        given `original` and `processed` nuumpy arrays to
        obtain the processed one but affected only as the
        selection mask says.

        The input are processed as float32, with float 
        precission, to be able to calculate properly,
        and then returned to uint8 [0, 255] values (the
        ones our OpenGL is able to handle with the 'f1'
        dtype and the sampler2d uniforms).
        """
        # We force to have float precission for the calculations
        original_input = TextureUtils.numpy_to_float32(original_input)
        processed_input = TextureUtils.numpy_to_float32(processed_input)
        selection_mask_input = TextureUtils.numpy_to_float32(selection_mask_input)

        # We need a 3D or 4D mask
        selection_mask_input = (
            np.expand_dims(selection_mask_input, axis = -1)
            if selection_mask_input.ndim == 2 else
            selection_mask_input
        )

        selection_mask_input = (
            np.repeat(
                a = selection_mask_input,
                repeats = original_input.shape[-1],
                axis = -1
            )
            if (
                selection_mask_input.shape[-1] == 1 and
                original_input.shape[-1] in (3, 4)
            ) else
            selection_mask_input
        )

        # Mix with the selection mask
        final = original_input * (1.0 - selection_mask_input) + processed_input * selection_mask_input

        return TextureUtils.numpy_to_uint8(final)