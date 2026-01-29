# TODO: Should we keep this functionality (?)
# from yta_video_opengl.utils import texture_to_frame
from yta_editor_nodes_cpu.blender.utils import _validate_inputs_and_mix_weights, _ensure_uint8
from yta_editor_nodes_cpu.utils import InputHandler
from yta_programming.singleton import SingletonABCMeta
from yta_validation.parameter import ParameterValidator
from abc import ABC, abstractmethod
from typing import Union

import numpy as np


class _BlenderCPU(ABC):
    """
    *For internal use only*

    Class to represent a blender that uses CPU to
    blend the inputs.

    This class must be implemented by any blender
    that uses CPU to blend inputs.
    """

    def __init__(
        self,
        blender: '_BlenderCoreCPU'
    ):
        self.blender: '_BlenderCoreCPU' = blender
        """
        The blender singleton instance that will be used
        internally to blend the inputs.
        """

    # TODO: Should this be in the '_BlenderCPU' instead (?)
    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        mix_weight: float = 1.0,
        dtype: Union[np.dtype, None] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Blend the `base_input` provided with the also given
        `overlay_input`, using the `mix_weight` to obtain
        a single output as the result.

        The inputs should be received in uint8 format in
        the [0, 255] range, then processed with the specific
        processing method, and then turned back again to the
        uint8 format and [0, 255] range.
        """
        return self.blender.process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            mix_weight = mix_weight,
            dtype = dtype,
            **kwargs
        )
    
    # TODO: Should this be in the '_BlenderCPU' instead (?)
    def process_multiple_inputs(
        self,
        inputs: list[np.ndarray],
        output_size: Union[tuple[int, int], None],
        mix_weights: Union[list[float], float] = 1.0,
        dtype: Union[np.dtype, None] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Blend all the `inputs` provided, one after another,
        applying the `mix_weight` provided, and forcing the
        result to the `dtype` if provided.

        The `mix_weight` can be a single float value, that 
        will be used for all the mixings, or a list of as
        many float values as `inputs` received, to be 
        applied individually to each mixing.
        """
        return self.blender.process_multiple_inputs(
            inputs = inputs,
            output_size = output_size,
            mix_weights = mix_weights,
            dtype = dtype,
            **kwargs
        )

class _BlenderCoreCPU(metaclass = SingletonABCMeta):
    """
    *Singleton class*

    *For internal use only*
    """

    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        mix_weight: float = 1.0,
        dtype: Union[np.dtype, None] = None,
        **kwargs
    # TODO: Is this the expected type (?)
    # TODO: What about OpenGL textures (?)
    ) -> np.ndarray:
        """
        Blend the `base_input` provided with the also given
        `overlay_input`, using the `mix_weight` to obtain
        a single output as the result.

        The inputs should be received in uint8 format in
        the [0, 255] range, then processed with the specific
        processing method, and then turned back again to the
        uint8 format and [0, 255] range.
        """
        ParameterValidator.validate_mandatory_instance_of('base_input', base_input, [np.ndarray, 'moderngl.Texture'])
        ParameterValidator.validate_mandatory_instance_of('overlay_input', overlay_input, [np.ndarray, 'moderngl.Texture'])
        ParameterValidator.validate_mandatory_number_between('mix_weight', mix_weight, 0.0, 1.0)

        # TODO: We should always receive the inputs as
        # uint8 in [0, 255] range

        # We will force the same size for the inputs
        """
        By now the strategy we are applying is to scale
        all the inputs to the size of the biggest one.
        TODO: Create more strategies and add a setting
        to be able to choose it
        """
        base_input, overlay_input = InputHandler.scale_to_biggest(
            inputs = [base_input, overlay_input]
        )

        # TODO: We have to make sure the sizes are the
        # same, or force them or do something...
        _validate_inputs_and_mix_weights(
            inputs = [base_input, overlay_input],
            mix_weights = [mix_weight]
        )

        # TODO: Should we keep this functionality (?)
        # Transform to numpy arrays if textures received
        # base_input = (
        #     texture_to_frame(base_input, do_include_alpha = True)
        #     if PythonValidator.is_instance_of(base_input, 'moderngl.Texture') else
        #     base_input
        # )

        # overlay_input = (
        #     texture_to_frame(overlay_input, do_include_alpha = True)
        #     if PythonValidator.is_instance_of(overlay_input, 'moderngl.Texture') else
        #     overlay_input
        # )

        dtype = (
            base_input.dtype
            if dtype is None else
            dtype
        )

        # TODO: Size of 'base_input' and 'overlay_input' must
        # be the same, and the 'base_input' should be the size
        if mix_weight == 0:
            # We want to affect 0% to the base, so we return the
            # base directly instead of calculating, but... Y_Y
            return base_input

        # 1. Blend with the specific internal process
        blended = self._blend(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            **kwargs
        )

        # 2. Apply mix_weight to determine the percentage to affect
        blended = (
            base_input * (1 - mix_weight) + blended * mix_weight
            if mix_weight < 1.0 else
            blended
        )

        # Always turn back to uint8 in [0, 255] range
        blended = _ensure_uint8(blended)

        return blended.astype(dtype)

    def process_multiple_inputs(
        self,
        inputs: list[np.ndarray],
        output_size: Union[tuple[int, int], None],
        mix_weights: Union[list[float], float] = 1.0,
        dtype: Union[np.dtype, None] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Blend all the `inputs` provided, one after another,
        applying the `mix_weight` provided, and forcing the
        result to the `dtype` if provided.

        The `mix_weight` can be a single float value, that 
        will be used for all the mixings, or a list of as
        many float values as `inputs` received, to be 
        applied individually to each mixing.
        """
        inputs = InputHandler.scale_to_biggest(
            inputs = inputs
        )

        _validate_inputs_and_mix_weights(
            inputs = inputs,
            mix_weights = mix_weights
        )
        
        # We process all the 'inputs' as 'base' and 'overlay'
        # and accumulate the result
        dtype = (
            inputs[0].dtype
            if dtype is None else
            dtype
        )

        # Use the first one as the base
        base = inputs[0]

        # TODO: How do we handle the additional parameters that
        # could be an array? Maybe if it is an array, check that
        # the number of elements is the same as the number of
        # inputs, and if a single value just use it...

        for i in range(1, len(inputs)):
            overlay = inputs[i]
            mix_weight = mix_weights[i]

            # TODO: If we make a lot of different operations and
            # force the [0, 255] range in each of them, we could
            # have an accumulated error... Think if we need to
            # refactor this
            base = self.process(
                base_input = base,
                overlay_input = overlay,
                output_size = output_size,
                mix_weight = mix_weight
            )

        # Result is always forced to uint8 and [0, 255] when
        # processed by pairs, so we don't need  to do it
        # TODO: Maybe we can avoid 'dtype' parameter as it
        # is not useful at all...
        return base.astype(dtype)
    
    @abstractmethod
    def _blend(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        **kwargs
    # TODO: Is this the expected type (?)
    # TODO: What about OpenGL textures (?)
    ) -> np.ndarray:
        """
        *For internal use only*

        *This method must be overwritten by the specific
        classes*

        The internal process to blend and mix the provided
        `base_input` and `overlay_input`.

        This method should not force uint8 nor [0, 255]
        range by itself as it would be done in the 'blend'
        main method.
        """
        pass