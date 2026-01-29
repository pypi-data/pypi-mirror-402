"""
This is the nodes module, in which we have
all the classes that make the concept work.

This module is specific to process with CPU.

You have access to a node that can be
instantiated as many times as you need, with
different parameters, that will call a 
singleton instance in the backend to process
the inputs.

Note for the developer:
- Make sure you use 'f1' dtype with [0, 255]
values (np.uint8) for the inputs, using the
float precission sometimes but always returning
those inputs for the textures because those are 
the ones we can handle with our OpenGL system.

IMPORTANT NOTES:
- The `input` for the CPU nodes must be `float32`
and the output will be given as a `float32`.
"""