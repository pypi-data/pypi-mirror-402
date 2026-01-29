from yta_editor_nodes_cpu.processor.abstract import _NodeProcessorCPU, _NodeProcessorCoreCPU
from abc import abstractmethod
from typing import Union

import numpy as np


class _VideoNodeProcessorCPU(_NodeProcessorCPU):
    """
    *Abstract class*

    Node class, which is to implement specific
    parameters when instantiated and also a specific
    node processor that will process the `input` for
    the `t` time moment provided, because this is to
    affect a frame of a specitic moment of a video.
    """

    def __init__(
        self,
        node_processor: '_VideoNodeProcessorCoreCPU'
    ):
        # TODO: Validate that is '_VideoNodeProcessorCoreCPU'
        super().__init__(
            node_processor = node_processor
        )

    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        t: float,
        **kwargs
    ) -> np.ndarray:
        """
        Process the provided `input` and transform it by
        using the code that is defined here according to
        the `t` time moment provided.
        """
        return self.node_processor.process(
            input = input,
            output_size = output_size,
            t = t
        )

class _VideoNodeProcessorCoreCPU(_NodeProcessorCoreCPU):
    """
    *Singleton class*

    *For internal use only*

    Class to represent a node processor that uses CPU
    to transform the input but it is meant to video
    processing, so it implements a 'time' parameter to
    manipulate the frames according to that time
    moment. This class will be called internally by the
    specific nodes to process the inputs.
    """

    # TODO: Just code and the same attributes that the
    # GPU version also has
    @abstractmethod
    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        t: float,
        **kwargs
    ) -> np.ndarray:
        """
        Process the provided `input` and transform it by
        using the code that is defined here according to
        the `t` time moment provided.
        """
        # TODO: Specific attributes can be received as
        # **kwargs to modify the specific process
        pass