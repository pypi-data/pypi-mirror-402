"""
We don't name it 'blend' instead of 'process' because
the GPU classes have the 'process' name due to the
inheritance from OpenGL classes, and we want to avoid
misunderstandings.
"""
from yta_editor_nodes_cpu.blender.add import AddBlenderCPU
from yta_editor_nodes_cpu.blender.alpha import AlphaBlenderCPU
from yta_editor_nodes_cpu.blender.mix import MixBlenderCPU


__all__ = [
    'AddBlenderCPU',
    'AlphaBlenderCPU',
    'MixBlenderCPU'
]