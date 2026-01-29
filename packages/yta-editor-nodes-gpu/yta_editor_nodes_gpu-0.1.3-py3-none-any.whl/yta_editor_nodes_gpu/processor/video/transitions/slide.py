from yta_editor_nodes_gpu.processor.video.transitions.abstract import _TransitionNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


# TODO: Create a parameter to chose the side
class _SlideTransitionPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to transition between the frames
    of 2 videos that slide from one side, hiding the
    first one and showing the second one.

    This pipeline is specific and unique for its the
    Node with the same name.
    """

    @property
    def fragment_shader(
        self
    ):
        return (
            '''
            #version 330
            uniform sampler2D first_texture;
            uniform sampler2D second_texture;
            uniform float progress;     // 0.0 → full A, 1.0 → full B
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                // Horizontal version (slide to right)
                //vec2 uv_first = v_uv + vec2(-progress, 0.0);
                //vec2 uv_second = v_uv + vec2(1.0 - progress, 0.0);

                // Horizontal version (slide to left)
                vec2 uv_first = v_uv + vec2(progress, 0.0);
                vec2 uv_second = v_uv + vec2(-1.0 + progress, 0.0);

                vec4 color_first = texture(first_texture, uv_first);
                vec4 color_second = texture(second_texture, uv_second);

                // Horizontal version (slide to right)
                //if (uv_first.x < 0.0) {
                //    output_color = color_second;
                //} else if (uv_second.x > 1.0) {
                //    output_color = color_first;
                //} else {
                //    // A and B frames are shown at the same time
                //    output_color = mix(color_first, color_second, progress);
                //}

                // Horizontal version (slide t o left)
                if (uv_first.x > 1.0) {
                    output_color = color_second;
                } else if (uv_second.x < 0.0) {
                    output_color = color_first;
                } else {
                    output_color = mix(color_first, color_second, progress);
                }
            }
            '''
        )
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'first_texture': 0,
            'second_texture': 1
        }
    
class SlideTransitionNodeProcessorGPU(_TransitionNodeProcessorGPU):
    """
    A node to modify the color of the textures we
    receive as input by transforming into a breathing
    frame.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _SlideTransitionPipelineGPU(
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
            progress = progress
        )