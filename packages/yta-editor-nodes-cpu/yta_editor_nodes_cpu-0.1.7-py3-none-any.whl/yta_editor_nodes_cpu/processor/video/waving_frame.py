from yta_editor_nodes_cpu.processor.video.abstract import _VideoNodeProcessorCoreCPU, _VideoNodeProcessorCPU
from yta_programming.decorators.requires_dependency import requires_dependency
from typing import Union

import numpy as np


class WavingFrameVideoNodeProcessorCPU(_VideoNodeProcessorCPU):
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
            node_processor = WavingFrameVideoNodeProcessorCoreCPU()
        )

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        t: float,
        amplitude: float = 0.05,
        frequency: float = 10.0,
        speed: float = 2.0,
        do_use_transparent_pixels: bool = False
    ) -> np.ndarray:
        """
        Process the `input` provided by using the node
        processor instance associated to this node and
        return the output.
        """
        return self.node_processor.process(
            input = input,
            output_size = output_size,
            t = t,
            amplitude = amplitude,
            frequency = frequency,
            speed = speed,
            do_use_transparent_pixels = do_use_transparent_pixels,
        )

class WavingFrameVideoNodeProcessorCoreCPU(_VideoNodeProcessorCoreCPU):
    """
    *Optional `opencv-python` (imported as `cv2`) library is required*
    
    Just an example of a specific class that is a node
    processor that uses CPU.
    """

    @requires_dependency('cv2', 'yta_editor_nodes_cpu', 'opencv-python')
    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        t: float,
        amplitude: float = 0.05,
        frequency: float = 10.0,
        speed: float = 2.0,
        do_use_transparent_pixels: bool = False
    ) -> np.ndarray:
        """
        Process the provided 'input' and transform it by
        using the code that is defined here.
        """
        import numpy as np
        import cv2  # opcional, solo para redimensionar/interpolar

        h, w, _ = input.shape

        # if input.shape[2] == 3:
        #     # Add alpha if needed
        #     input = cv2.cvtColor(input, cv2.COLOR_BRG2BRGA)

        # UV coordinates [0, 1]
        x = np.linspace(0, 1, w, dtype = np.float32)
        y = np.linspace(0, 1, h, dtype = np.float32)
        xv, yv = np.meshgrid(x, y)
        # Flip vertically to match OpenGL (GPU) orientation
        yv = 1.0 - yv  

        wave = np.sin(xv * frequency + t * speed) * amplitude

        # UV coordinates displacement
        yv_new = yv + wave

        # UV coordinates to pixels
        map_x = (xv * (w - 1)).astype(np.float32)
        # Invert back for image space (to be similar to GPU effect)
        map_y = ((1.0 - yv_new) * (h - 1)).astype(np.float32)

        output = cv2.remap(
            input,
            map_x,
            map_y,
            interpolation = cv2.INTER_LINEAR,
            borderMode = cv2.BORDER_REFLECT
        )

        if do_use_transparent_pixels:
            mask = (yv_new < 0.0) | (yv_new > 1.0)
            output[mask, 3] = 0

        return output