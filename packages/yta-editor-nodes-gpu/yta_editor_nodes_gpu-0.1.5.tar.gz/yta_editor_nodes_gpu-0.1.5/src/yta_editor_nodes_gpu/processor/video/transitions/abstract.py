from yta_video_opengl.new.opengl_nodes import _FirstAndSecondTexturesOpenGLNode
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl

    
class _TransitionNodeProcessorGPU(_FirstAndSecondTexturesOpenGLNode):
    """
    *For internal use only*

    Class to represent a node processor that uses GPU
    to build a transition from one video to another.

    The shader is using two inputs called `first_texture`
    and `second_texture`.
    """

    def process(
        self,
        first_input: moderngl.Texture,
        second_input: moderngl.Texture,
        progress: float,
        output_size: Union[tuple[int, int], None] = None,
        **kwargs
    ) -> moderngl.Texture:
        """
        Validate the parameters, set the textures map, process
        it and return the result according to the `progress`
        provided.

        You can provide any additional parameter
        in the **kwargs, but be careful because
        this could overwrite other uniforms that
        were previously set.

        We use and return textures to maintain
        the process in GPU and optimize it.
        """
        ParameterValidator.validate_mandatory_instance_of('first_input', first_input, moderngl.Texture)
        ParameterValidator.validate_mandatory_instance_of('second_input', second_input, moderngl.Texture)
        ParameterValidator.validate_mandatory_positive_float('progress', progress, do_include_zero = True)

        textures_map = {
            'first_texture': first_input,
            'second_texture': second_input
        }

        return self._process_common(
            textures_map = textures_map,
            output_size = output_size,
            progress = progress,
            **kwargs
        )