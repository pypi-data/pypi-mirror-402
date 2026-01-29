from yta_editor_nodes_cpu.blender.abstract import _BlenderCoreCPU, _BlenderCPU
from typing import Union

import numpy as np


class MixBlenderCPU(_BlenderCPU):
    """
    Blend the second input with the first one
    applying the float factor (between 0.0 and
    1.0) that is passed as parameter.
    """

    def __init__(
        self
    ):
        super().__init__(
            blender = _MixBlenderCoreCPU()
        )

class _MixBlenderCoreCPU(_BlenderCoreCPU):
    """
    *Singleton class*

    *For internal use only*

    Blend the second input with the first one
    applying the float factor (between 0.0 and
    1.0) that is passed as parameter.
    """

    def _blend(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        mix_weight: float = 1.0
    ) -> np.ndarray:
        """
        *For internal use only*

        The internal process to blend and mix the provided
        `base_input` and `overlay_input`.

        This method should not force uint8 nor [0, 255]
        range by itself as it would be done in the 'blend'
        main method.
        """
        # We do nothing because the mix is done in the
        # general 'process' method that calls this one
        # TODO: Maybe obtain the 'output_size' from
        # the 'overlay_input' if not defined...
        return overlay_input