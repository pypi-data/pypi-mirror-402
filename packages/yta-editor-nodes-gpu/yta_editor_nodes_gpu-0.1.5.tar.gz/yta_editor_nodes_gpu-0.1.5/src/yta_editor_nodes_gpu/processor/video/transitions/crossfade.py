from yta_editor_nodes_gpu.processor.video.transitions.abstract import _TransitionNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


class _CrossfadeTransitionPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to transition between the frames
    of 2 videos that, transforming the first one into
    the second one.

    This pipeline is specific and unique for its the
    Node with the same name.
    """

    @property
    def fragment_shader(
        self
    ):
        return (
            """
            #version 330
            uniform sampler2D first_texture;
            uniform sampler2D second_texture;
            uniform float progress; // 0 = full A, 1 = full B
            in vec2 v_uv;
            out vec4 output_color;
            void main() {
                vec4 color_first = texture(first_texture, v_uv);
                vec4 color_second = texture(second_texture, v_uv);
                output_color = mix(color_first, color_second, progress);
            }
            """
        )
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'first_texture': 0,
            'second_texture': 1
        }
    
class CrossfadeTransitionNodeProcessorGPU(_TransitionNodeProcessorGPU):
    """
    A node to transition between the frames of 2 videos
    transforming the first one into the second one.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _CrossfadeTransitionPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        first_input: moderngl.Texture,
        second_input: moderngl.Texture,
        progress: float,
        output_size: Union[tuple[int, int], None] = None
    ) -> moderngl.Texture:
        """
        Validate the parameters, set the textures map,
        process it and return the result according to the
        `progress` provided.

        We use and return textures to maintain the
        process in GPU and optimize it.
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
            progress = progress
        )