from yta_editor_nodes_cpu.blender.abstract import _BlenderCoreCPU, _BlenderCPU
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class AddBlenderCPU(_BlenderCPU):
    """
    Blend the different inputs by applying the
    normal and most famous alpha blending and the
    most typical used in video editing.

    This blender will increase the brightness by
    combining the colors of the base and the overlay
    inputs, using the overlay as much as the 
    `stregth` parameter is indicating.
    """

    def __init__(
        self
    ):
        super().__init__(
            blender = _AddBlenderCoreCPU()
        )

class _AddBlenderCoreCPU(_BlenderCoreCPU):
    """
    *Singleton class*

    *For internal use only*

    Blend the different inputs by applying the
    normal and most famous alpha blending and the
    most typical used in video editing.

    This blender will increase the brightness by
    combining the colors of the base and the overlay
    inputs, using the overlay as much as the 
    `stregth` parameter is indicating.
    """
    
    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        mix_weight: float = 1.0,
        dtype: Union[np.dtype, None] = None,
        strength: float = 1.0
    ) -> np.ndarray:
        # TODO: Maybe obtain the 'output_size' from
        # the 'base_input' if not defined...
        return super().process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            mix_weight = mix_weight,
            dtype = dtype,
            strength = strength
        )
    
    def _blend(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        strength: float = 1.0
    ) -> np.ndarray:
        """
        *For internal use only*

        The internal process to blend and mix the provided
        `base_input` and `overlay_input`.

        This method should not force uint8 nor [0, 255]
        range by itself as it would be done in the 'blend'
        main method.
        """
        # We force to have float precission for the calculations
        base_input = TextureUtils.numpy_to_float32(base_input)
        overlay_input = TextureUtils.numpy_to_float32(overlay_input)

        # Add blending (base + overlay * strength)
        result = base_input + overlay_input * strength

        return TextureUtils.numpy_to_uint8(np.clip(result, 0.0, 1.0))