from yta_editor_nodes_gpu.processor.abstract import _NodeProcessorGPU
from typing import Union

import moderngl


class _VideoNodeProcessorGPU(_NodeProcessorGPU):
    """
    *Abstract class*

    *Singleton class*

    *For internal use only*

    Class to represent a node processor that uses GPU
    to transform the input but it is meant to video
    processing, so it implements a `t` parameter to
    manipulate the frames according to that time
    moment.

    This class must be implemented by any processor
    that uses GPU to modify an input.
    """

    def process(
        self,
        input: moderngl.Texture,
        t: float,
        output_size: Union[tuple[int, int], None] = None,
        **dynamic_uniforms
    ) -> moderngl.Texture:
        """
        Process the `input` provided and get an output of
        the given `output_size` and for the `t` time
        moment provided, by using the `**dynamic_uniforms`
        if needed.
        """
        return super().process(
            input = input,
            output_size = output_size,
            t = t,
            **dynamic_uniforms
        )
