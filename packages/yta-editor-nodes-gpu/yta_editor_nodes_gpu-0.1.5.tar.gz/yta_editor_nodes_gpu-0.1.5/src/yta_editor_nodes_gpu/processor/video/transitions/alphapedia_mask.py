from yta_editor_nodes_gpu.processor.video.transitions.abstract import _TransitionNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


class _AlphaPediaMaskTransitionPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to transition between the frames
    of 2 videos that, using a custom mask to join the
    2 videos. This mask is specifically obtained from
    the AlphaPediaYT channel in which we upload
    specific masking videos.

    Both videos will be placed occupying the whole
    scene, just overlapping by using the transition
    video mask, but not moving the frame through 
    the screen like other classes do (like the
    FallingBars).

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
            uniform sampler2D mask_texture;

            uniform float progress;  // 0.0 → full A, 1.0 → full B
            uniform bool use_alpha_channel;   // True to use the alpha channel
            //uniform float contrast;  // Optional contrast to magnify the result

            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                vec4 first_color = texture(first_texture, v_uv);
                vec4 second_color = texture(second_texture, v_uv);
                vec4 mask_color = texture(mask_texture, v_uv);

                // Mask alpha or red?
                float mask_value = use_alpha_channel ? mask_color.a : mask_color.r;

                // Optional contrast
                //mask_value = clamp((mask_value - 0.5) * contrast + 0.5, 0.0, 1.0);
                mask_value = clamp((mask_value - 0.5) + 0.5, 0.0, 1.0);

                float t = smoothstep(0.0, 1.0, mask_value + progress - 0.5);

                output_color = mix(first_color, second_color, t);
            }
            """
        )
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'first_texture': 0,
            'second_texture': 1,
            'mask_texture': 2
        }
    
class AlphaPediaMaskTransitionNodeProcessorGPU(_TransitionNodeProcessorGPU):
    """
    A node to transition between the frames of 2 videos
    using a custom mask to join the 2 videos. This mask
    is specifically obtained from the AlphaPediaYT
    channel in which we upload specific masking videos.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _AlphaPediaMaskTransitionPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        first_input: moderngl.Texture,
        second_input: moderngl.Texture,
        mask_input: moderngl.Texture,
        progress: float,
        output_size: Union[tuple[int, int], None] = None
    ) -> moderngl.Texture:
        """
        Mix the `first_input` with the `second_input`
        based on the `progress` given and using the
        `mask_input` provided.

        We use and return textures to maintain the
        process in GPU and optimize it.
        """
        ParameterValidator.validate_mandatory_instance_of('first_input', first_input, moderngl.Texture)
        ParameterValidator.validate_mandatory_instance_of('second_input', second_input, moderngl.Texture)
        ParameterValidator.validate_mandatory_instance_of('mask_input', mask_input, moderngl.Texture)
        ParameterValidator.validate_mandatory_positive_float('progress', progress, do_include_zero = True)

        textures_map = {
            'first_texture': first_input,
            'second_texture': second_input,
            'mask_texture': mask_input
        }

        # TODO: There is a 'use_alpha_channel' uniform to use
        # the alpha instead of the red color of the frame value,
        # but the red is working for our AlphaPedia videos, so...

        return self._process_common(
            textures_map = textures_map,
            output_size = output_size,
            progress = progress
        )