from yta_editor_nodes_cpu.processor.audio.abstract import _AudioNodeProcessorCoreCPU, _AudioNodeProcessorCPU

import numpy as np


class ChorusAudioNodeProcessorCPU(_AudioNodeProcessorCPU):
    """
    The audio node processor to apply a chorus
    effect.
    """

    def __init__(
        self,
        sample_rate: int,
        depth: int = 0,
        frequency: float = 0.25
    ):
        # TODO: Describe these attributes, please
        self.sample_rate: int = sample_rate
        self.depth: int = depth
        self.frequency: float = frequency

        super().__init__(
            audio_node_processor = _ChorusAudioNodeProcessorCoreCPU()
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
            sample_rate = self.sample_rate,
            depth = self.depth,
            frequency = self.frequency
        )
    
class _ChorusAudioNodeProcessorCoreCPU(_AudioNodeProcessorCoreCPU):
    """
    *For internal use only*

    *Singleton class*

    The audio node processor to apply a chorus
    effect.
    """

    def process(
        self,
        input: np.ndarray,
        t: float,
        sample_rate: int,
        depth: int,
        frequency: float
    ) -> np.ndarray:
        """
        Process the provided audio 'input' that
        is played on the given 't' time moment.
        """
        n_samples = input.shape[0]
        t = np.arange(n_samples) / sample_rate

        # Sinusoidal LFO that controls the delay
        delay = (depth / 1000.0) * sample_rate * (0.5 * (1 + np.sin(2 * np.pi * frequency * t)))
        delay = delay.astype(np.int32)

        output = np.zeros_like(input, dtype=np.float32)

        for i in range(n_samples):
            d = delay[i]

            output[i]= (
                0.7 * input[i] + 0.7 * input[i - d]
                if (i - d) >= 0 else
                input[i]
            )

        return output