"""
When working with audio frames, we don't need
to use the GPU because audios are 1D and the
information can be processed perfectly with
a library like numpy.

If we need a very intense calculation for an
audio frame (FFT, convolution, etc.) we can
use CuPy or some DPS specific libraries, but
90% is perfectly done with numpy.

If you want to modify huge amounts of audio
(some seconds at the same time), you can use
CuPy, that has the same API as numpy but
working in GPU. Doing this below most of the
changes would work:
- `import numpy as np` → `import cupy as np`
"""
from yta_editor_nodes_cpu.processor.audio.volume import VolumeAudioNodeProcessorCPU


__all__ = [
    'VolumeAudioNodeProcessorCPU'
]