from yta_programming.singleton import SingletonABCMeta
from abc import ABC, abstractmethod
from typing import Union

import numpy as np


class _NodeCompositorCPU(ABC):
    """
    *Abstract class*

    *For internal use only*

    Class to represent a node compositor that uses CPU
    to position the input in a specific place.

    Node class, which is to implement specific
    parameters when instantiated and also a specific
    node compositor that will process the `input`.

    This _NodeCompositor is to be able to make a composition
    with different inputs. For example, placing a specific
    input in a position, with a rotation, over another input
    that acts as the base.
    """

    def __init__(
        self,
        node_compositor: '_NodeCompositorCoreCPU'
    ):
        # TODO: Validate that is '_NodeCompositorCoreCPU' or child
        self.node_compositor: '_NodeCompositorCoreCPU' = node_compositor
        """
        The singleton instance of the compositor that will
        process the input and return the output.
        """

    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
        output_size: Union[tuple[int, int], None],
        **kwargs
    ) -> np.ndarray:
        """
        Process the provided 'input' and transform it by
        using the code that is defined here.
        """
        return self.node_compositor.process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size
        )

class _NodeCompositorCoreCPU(metaclass = SingletonABCMeta):
    """
    *Singleton class*

    *For internal use only*

    This class is to be able to make a composition with
    different inputs. For example, placing an input in a
    specific position, with a rotation, over another
    input that acts as the base.

    This class will be called internally by the specific
    nodes to make the composition.
    """

    # def __init__(
    #     self,
    #     **kwargs
    # ):
    #     pass

    # def __reinit__(
    #     self,
    #     **kwargs
    # ):
    #     pass
    
    # TODO: Just code and the same attributes that the
    # GPU version also has
    @abstractmethod
    def process(
        self,
        base_input: np.ndarray,
        overlay_input: np.ndarray,
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