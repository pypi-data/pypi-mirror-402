"""
The nodes that modify inputs by using static parameters
and not 't' time moments, with CPU.
"""
from yta_editor_nodes_cpu.processor.black_and_white import BlackAndWhiteNodeProcessorCPU
from yta_editor_nodes_cpu.processor.brightness import BrightnessNodeProcessorCPU
from yta_editor_nodes_cpu.processor.color_contrast import ColorContrastNodeProcessorCPU
from yta_editor_nodes_cpu.processor.selection_mask import SelectionMaskNodeProcessorCPU


__all__ = [
    'BlackAndWhiteNodeProcessorCPU',
    'BrightnessNodeProcessorCPU',
    'ColorContrastNodeProcessorCPU',
    'SelectionMaskNodeProcessorCPU'
]
    
