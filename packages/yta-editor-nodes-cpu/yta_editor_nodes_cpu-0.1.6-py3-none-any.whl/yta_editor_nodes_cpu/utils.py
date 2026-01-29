from yta_programming.decorators.requires_dependency import requires_dependency
from yta_validation.parameter import ParameterValidator

import numpy as np


class InputHandler:
    """
    Class with static methods to simplify the way
    we handle the inputs to make them have the same
    size, able to be used in the nodes.
    """

    # TODO: Untested
    @staticmethod
    def pad(
        input: np.ndarray,
        size: tuple[int, int]
    ) -> np.ndarray:
        """
        Pad the `input` provided to fit the given `size`
        by adding transparent pixels around it and
        leaving the original input centered.
        """
        if input.ndim != 3:
            raise Exception(f'Expected shape (H, w, C), got {input.shape}')
        
        height, width, number_of_channels = input.shape

        if (width, height) > size:
            raise Exception('The input is bigger than the "size" requested.')
        elif (width, height) == size:
            return input
        
        # --- Normalizar a RGBA ---
        if number_of_channels == 3:
            alpha = np.full(
                shape = (height, width, 1),
                fill_value = 255,
                dtype = input.dtype
            )
            a_rgba = np.concatenate(
                arrays = [input, alpha],
                axis = 2
            )
        elif number_of_channels == 4:
            a_rgba = input
        else:
            raise Exception(f'Unexpected number of channels: {str(number_of_channels)}')

        # Transparent canvas
        canvas = np.zeros(
            shape = (size[1], size[0], 4),
            dtype = input.dtype
        )

        # --- Calcular offsets para centrar ---
        y0 = (size[1] - height) // 2
        x0 = (size[0] - width) // 2

        # --- Insertar imagen ---
        canvas[y0:y0 + height, x0:x0 + width] = a_rgba

        return canvas
    
    @requires_dependency('PIL', 'yta_numpy', 'pillow')
    def scale_to_biggest(
        inputs: list[np.ndarray]
    ) -> list[np.ndarray]:
        """
        Prepare all the `inputs` provided to have the same
        size (the size of the biggest one) by scalling them
        using pillow (`PIL`).
        """
        from yta_numpy.utils import scale_numpy_pillow

        ParameterValidator.validate_mandatory_list_of_these_instances('inputs', inputs, np.ndarray)

        # Look for the biggest size
        max_width = max(input.shape[1] for input in inputs)
        max_height = max(input.shape[0] for input in inputs)
        max_size: tuple[int, int] = (max_width, max_height)

        return [
            (
                # Scale if needed
                scale_numpy_pillow(input, max_size)
                if (input.shape[1], input.shape[0]) < max_size else
                input
            )
            for input in inputs
        ]
