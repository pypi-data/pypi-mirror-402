from yta_programming.singleton import SingletonABCMeta
from abc import ABC, abstractmethod

import numpy as np


class _AudioNodeProcessorCPU(ABC):
    """
    *For internal use only*

    *Abstract class*

    Node class, which is to implement specific
    parameters when instantiated and also a specific
    audio node processor that will process the
    `input` provided for a `t` time moment.
    """

    def __init__(
        self,
        audio_node_processor: '_AudioNodeProcessorCoreCPU'
    ):
        # TODO: Validate that is '_AudioNodeProcessorCoreCPU' or child
        self.audio_node_processor: '_AudioNodeProcessorCoreCPU' = audio_node_processor
        """
        The singleton instance of the processor that will
        process the input and return the output.
        """

    def process(
        self,
        input: np.ndarray,
        t: float,
        **kwargs
    ) -> np.ndarray:
        """
        Process the provided audio `input` that
        is played on the given `t` time moment.
        """
        return self.audio_node_processor.process(
            input = input,
            t = t,
            **kwargs
        )

class _AudioNodeProcessorCoreCPU(metaclass = SingletonABCMeta):
    """
    *For internal use only*

    *Singleton class*

    The processor core that will be called by the
    specific audio node.
    """

    @abstractmethod
    def process(
        self,
        input: np.ndarray,
        t: float,
        **kwargs
    ) -> np.ndarray:
        """
        Process the provided audio `input` that
        is played on the given `t` time moment.
        """
        pass