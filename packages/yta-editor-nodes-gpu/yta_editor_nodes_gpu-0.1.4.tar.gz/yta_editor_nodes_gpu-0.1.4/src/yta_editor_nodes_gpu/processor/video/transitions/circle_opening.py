from yta_editor_nodes_gpu.processor.video.transitions.abstract import _TransitionNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


class _CircleOpeningTransitionPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to transition between the frames
    of 2 videos in which the frames are mixed by
    generating a circle that grows from the middle to
    end fitting the whole screen.

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
            #define UNIQUE_ID_{id(self)}
            uniform sampler2D first_texture;
            uniform sampler2D second_texture;
            uniform float progress;  // 0.0 → full A, 1.0 → full B
            uniform float border_smoothness; // 0.02 is a good value

            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                // Obtain the size automatically from the texture
                vec2 output_size = vec2(textureSize(first_texture, 0));

                vec2 pos = v_uv * output_size;
                vec2 center = output_size * 0.5;

                // Distance from center
                float dist = distance(pos, center);

                // Radius of current circle
                float max_radius = length(center);
                float radius = progress * max_radius;

                vec4 first_color = texture(first_texture, v_uv);
                vec4 second_color = texture(second_texture, v_uv);

                // With smooth circle
                // TODO: Make this customizable
                float mask = 1.0 - smoothstep(radius - border_smoothness * max_radius, radius + border_smoothness * max_radius, dist);
                output_color = mix(first_color, second_color, mask);
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
    
class CircleOpeningTransitionNodeProcessorGPU(_TransitionNodeProcessorGPU):
    """
    A transition between the frames of 2 videos in
    which the frames are mixed by generating a circle
    that grows from the middle to end fitting the whole
    screen.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None,
        border_smoothness = 0.02
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _CircleOpeningTransitionPipelineGPU(
                opengl_context = opengl_context
            ),
            border_smoothness = border_smoothness
        )

    def process(
        self,
        first_input: moderngl.Texture,
        second_input: moderngl.Texture,
        progress: float,
        output_size: Union[tuple[int, int], None] = None,
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