from yta_editor_nodes_cpu.complex.abstract import _NodeComplexCoreCPU, _NodeComplexCPU

import numpy as np


class DisplayOverAtNodeComplexCPU(_NodeComplexCPU):
    """
    The overlay input is placed in the scene with the
    given position, rotation and size, and then put as
    an overlay of the also given base input.

    Information:
    - The scene size is `(1920, 1080)`, so provide the
    `position` parameter according to it, where it is
    representing the center of the texture.
    - The `rotation` is in degrees, where `rotation=90`
    means rotating 90 degrees to the right.
    - The `size` parameter must be provided according to
    the previously mentioned scene size `(1920, 1080)`.
    """

    def __init__(
        self
    ):
        super().__init__(
            node_complex = _DisplayOverAtNodeComplexCoreCPU()
        )

    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: tuple[int, int] = (1920, 1080),
        position: tuple[int, int] = (1920 / 2, 1080 / 2),
        size: tuple[int, int] = (1920 / 2, 1080 / 2),
        rotation: int = 0
    ) -> np.ndarray:
        return self.node_complex.process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            position = position,
            rotation = rotation,
            size = size
        )

class _DisplayOverAtNodeComplexCoreCPU(_NodeComplexCoreCPU):
    """
    *For internal use only*

    The overlay input is placed in the scene with the
    given position, rotation and size, and then put as
    an overlay of the also given base input.

    Information:
    - The scene size is `(1920, 1080)`, so provide the
    `position` parameter according to it, where it is
    representing the center of the texture.
    - The `rotation` is in degrees, where `rotation=90`
    means rotating 90 degrees to the right.
    - The `size` (of the element to display) parameter
    must be provided according to the previously
    mentioned scene size `(1920, 1080)`.

    TODO: This has no inheritance, is special and we need
    to be able to identify it as a valid one.

    TODO: This must be implemented
    """

    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: tuple[int, int] = (1920, 1080),
        position: tuple[int, int] = (1920 / 2, 1080 / 2),
        size: tuple[int, int] = (1920 / 2, 1080 / 2),
        rotation: int = 0
    ) -> np.ndarray:
        raise NotImplementedError('Not implemented yet')