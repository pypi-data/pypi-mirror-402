from yta_programming.singleton import SingletonABCMeta
from abc import ABC, abstractmethod
from typing import Union

import numpy as np


class _NodeComplexCPU(ABC):
    """
    *For internal use only*

    *Abstract class*

    A node that is made by applying different nodes. It
    is different than the other nodes because it needs
    to import different nodes to process the input(s),
    by using CPU.
    """

    def __init__(
        self,
        node_complex: '_NodeComplexCoreCPU'
    ):
        # TODO: Validate that is 'NodeComplexCoreCPU' or child
        self.node_complex: '_NodeComplexCoreCPU' = node_complex
        """
        The singleton instance of the complex node that
        will process the input and return the output.
        """

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
        return self.node_complex.process(
            input = input,
            output_size = output_size,
            **kwargs
        )
    
class _NodeComplexCoreCPU(metaclass = SingletonABCMeta):
    """
    *For internal use only*

    *Singleton class*

    This class is to be able to use different nodes with
    the same input.

    This class will be called internally by the specific
    nodes to make the composition.
    """

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
        pass