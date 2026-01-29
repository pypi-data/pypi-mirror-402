from yta_editor_nodes_cpu.processor.audio.abstract import _AudioNodeProcessorCoreCPU, _AudioNodeProcessorCPU

import numpy as np


class VolumeAudioNodeProcessorCPU(_AudioNodeProcessorCPU):
    """
    The audio node processor to adjust the volume
    of the audio provided.
    """

    def __init__(
        self,
        # TODO: Maybe we need a `RateFunction` or similar
        factor_fn: callable
    ):
        self.factor_fn: callable = factor_fn
        """
        The function to calculate the `factor` to apply
        for a specific `t` time moment.
        """
        super().__init__(
            audio_node_processor = _VolumeAudioNodeProcessorCoreCPU()
        )

    def process(
        self,
        input: np.ndarray,
        t: float,
    ) -> np.ndarray:
        """
        Process the provided audio 'input' that
        is played on the given 't' time moment.
        """
        return self.audio_node_processor.process(
            input = input,
            t = t,
            factor_fn = self.factor_fn
        )

class _VolumeAudioNodeProcessorCoreCPU(_AudioNodeProcessorCoreCPU):
    """
    *For internal use only*

    *Singleton class*

    The audio node processor to adjust the volume
    of the audio provided.
    """

    def process(
        self,
        input: np.ndarray,
        t: float,
        # TODO: Maybe we need a `RateFunction` or similar
        factor_fn: callable
    ) -> np.ndarray:
        """
        Process the provided audio 'input' that is
        played on the given 't' time moment and adjust
        the volume by using the `factor_fn` provided.
        """
        # TODO: This is not ok, change it
        factor = factor_fn(t, 0)

        samples = input
        samples *= factor

        # Determine dtype according to format
        # samples = (
        #     samples.astype(np.int16)
        #     # 'fltp', 's16', 's16p'
        #     if 's16' in input.format.name else
        #     samples.astype(np.float32)
        # )

        return samples
