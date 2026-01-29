from yta_programming.singleton import SingletonABCMeta
from abc import ABC, abstractmethod
from typing import Union

import numpy as np


class _NodeProcessorCPU(ABC):
    """
    *Abstract class*

    *For internal use only*

    Node class, which is to implement specific
    parameters when instantiated and also a specific
    node processor that will process the `input`.
    """

    def __init__(
        self,
        node_processor: '_NodeProcessorCoreCPU'
    ):
        # TODO: Validate that is '_NodeProcessorCoreCPU' or child
        self.node_processor: '_NodeProcessorCoreCPU' = node_processor
        """
        The singleton instance of the processor that will
        process the input and return the output.
        """

class _NodeProcessorCoreCPU(metaclass = SingletonABCMeta):
    """
    *Singleton class*

    *For internal use only*

    Class to represent a node processor that uses CPU
    to transform the input. This class will be called
    internally by the specific nodes to process the
    inputs.
    """

    # TODO: Just code and the same attributes that the
    # GPU version also has
    @abstractmethod
    def process(
        self,
        input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        **kwargs
    ) -> np.ndarray:
        """
        Process the provided 'input' and transform it by
        using the code that is defined here.
        """
        # TODO: Specific attributes can be received as
        # **kwargs to modify the specific process
        pass