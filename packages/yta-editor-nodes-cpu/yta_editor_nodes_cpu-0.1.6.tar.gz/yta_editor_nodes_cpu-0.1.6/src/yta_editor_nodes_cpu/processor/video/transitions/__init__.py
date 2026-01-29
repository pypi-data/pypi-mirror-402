"""
TODO: This module doesn't use 't' but 'progress'
so it is not a child of 'processor.video', maybe
we should move it to be 'processor.transitions'
instead of 'processor.video.transitions'... (?)
"""
from yta_editor_nodes_cpu.processor.video.transitions.slide import SlideTransitionProcessorCPU


__all__ = [
    'SlideTransitionProcessorCPU'
]