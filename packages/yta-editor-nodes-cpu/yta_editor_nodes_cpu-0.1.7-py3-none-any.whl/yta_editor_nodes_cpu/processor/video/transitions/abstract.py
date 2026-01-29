from yta_editor_nodes_cpu.processor.abstract import _NodeProcessorCPU, _NodeProcessorCoreCPU
from abc import abstractmethod
from typing import Union

import numpy as np


class _TransitionProcessorCPU(_NodeProcessorCPU):
    """
    *For internal use only*

    A transition between the frames of 2 videos.

    This transition is made with CPU (numpy).
    """

    def __init__(
        self,
        node_processor: '_TransitionProcessorCoreCPU'
    ):
        # TODO: Validate '_TransitionProcessorCoreCPU' or child
        super().__init__(
            node_processor = node_processor
        )

    def process(
        self,
        first_input: np.ndarray,
        second_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        progress: float,
        **kwargs
    ) -> np.ndarray:
        """
        Process the `first_input` and `second_input` and
        generate the transition frame according to the
        `progress` of the transition provided.
        """
        return self.node_processor.process(
            first_input = first_input,
            second_input = second_input,
            output_size = output_size,
            progress = progress,
            **kwargs
        )
    

class _TransitionProcessorCoreCPU(_NodeProcessorCoreCPU):
    """
    *For internal use only*

    *Singleton class*

    Class to represent a transition in between 2
    different videos. This class will be called
    internally by the specific nodes to process
    the inputs.
    """

    @abstractmethod
    def process(
        self,
        first_input: np.ndarray,
        second_input: np.ndarray,
        progress: float,
        **kwargs
    ) -> np.ndarray:
        """
        Process the `first_input` and `second_input` and
        generate the transition frame according to the
        `progress` of the transition provided.
        """
        # TODO: Specific attributes can be received as
        # **kwargs to modify the specific process
        pass
    