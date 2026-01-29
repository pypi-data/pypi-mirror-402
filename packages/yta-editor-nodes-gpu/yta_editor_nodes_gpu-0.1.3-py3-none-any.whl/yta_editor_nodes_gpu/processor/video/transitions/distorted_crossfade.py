from yta_editor_nodes_gpu.processor.video.transitions.abstract import _TransitionNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


class _DistortedCrossfadeTransitionPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to transition between the frames
    of 2 videos that, transforming the first one into
    the second one with a distortion in between.

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
            uniform float progress;   // 0.0 -> A, 1.0 -> B
            uniform float intensity;  // Distortion control
            in vec2 v_uv;
            out vec4 output_color;

            const int passes = 6;

            void main() {
                vec4 c1 = vec4(0.0);
                vec4 c2 = vec4(0.0);

                float disp = intensity * (0.5 - distance(0.5, progress));
                for (int xi=0; xi<passes; xi++) {
                    float x = float(xi) / float(passes) - 0.5;
                    for (int yi=0; yi<passes; yi++) {
                        float y = float(yi) / float(passes) - 0.5;
                        vec2 v = vec2(x, y);
                        float d = disp;
                        c1 += texture(first_texture, v_uv + d * v);
                        c2 += texture(second_texture, v_uv + d * v);
                    }
                }
                c1 /= float(passes * passes);
                c2 /= float(passes * passes);
                output_color = mix(c1, c2, progress);
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
    
class DistortedCrossfadeTransitionNodeProcessorGPU(_TransitionNodeProcessorGPU):
    """
    A node to transition between the frames of 2 videos
    transforming the first one into the second one with
    a distortion in between
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None,
        intensity: float = 1.0,
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _DistortedCrossfadeTransitionPipelineGPU(
                opengl_context = opengl_context
            ),
            intensity = intensity
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