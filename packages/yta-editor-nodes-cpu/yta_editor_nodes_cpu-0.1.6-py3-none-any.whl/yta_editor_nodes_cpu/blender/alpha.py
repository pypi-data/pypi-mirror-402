from yta_editor_nodes_cpu.blender.abstract import _BlenderCoreCPU, _BlenderCPU
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class AlphaBlenderCPU(_BlenderCPU):
    """
    Blend the different inputs by applying the
    normal and most famous alpha blending and the
    most typical used in video editing.

    This blender will use the alpha channel of the 
    overlay input, multiplied by the `blend_strength`
    parameter provided, to use it as the mixer factor
    between the base and the overlay inputs.
    """

    def __init__(
        self
    ):
        super().__init__(
            blender = _AlphaBlenderCoreCPU()
        )

class _AlphaBlenderCoreCPU(_BlenderCoreCPU):
    """
    *Singleton class*

    *For internal use only*

    Blend the different inputs by applying the
    normal and most famous alpha blending and the
    most typical used in video editing.

    This blender will use the alpha channel of the 
    overlay input, multiplied by the `blend_strength`
    parameter provided, to use it as the mixer factor
    between the base and the overlay inputs.
    """
    
    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        mix_weight: float = 1.0,
        dtype: Union[np.dtype, None] = None,
        blend_strength: float = 0.5
    ) -> np.ndarray:
        # TODO: Maybe obtain the 'output_size' from
        # the 'base_input' if not defined...
        return super().process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            mix_weight = mix_weight,
            dtype = dtype,
            blend_strength = blend_strength
        )
    
    def _blend(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        blend_strength: float = 1.0
    ) -> np.ndarray:
        """
        *For internal use only*

        The internal process to blend and mix the provided
        `base_input` and `overlay_input`.

        (!) This method should not force uint8 nor [0, 255]
        range by itself as it would be done in the 'blend'
        main method.
        """
        # We force to have float precission for the calculations
        base_input = TextureUtils.numpy_to_float32(base_input)
        overlay_input = TextureUtils.numpy_to_float32(overlay_input)

        base_rgb, base_a = base_input[..., :3], base_input[..., 3:4]
        overlay_rgb, overlay_a = overlay_input[..., :3], overlay_input[..., 3:4]

        # Compound alpha
        alpha = overlay_a * blend_strength

        # Equivalent to mix(base, overlay, alpha) in glsl
        out_rgb = base_rgb * (1.0 - alpha) + overlay_rgb * alpha
        out_a = base_a * (1.0 - alpha) + overlay_a * alpha

        return TextureUtils.numpy_to_uint8(np.concatenate(
            [out_rgb, out_a],
            axis = -1
        ))