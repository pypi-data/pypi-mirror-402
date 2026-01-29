from yta_editor_nodes_gpu.blender.abstract import _NodeBlenderGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _AddBlenderPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    Blender to blend 2 textures by adding their values.

    This blender will increase the brightness by
    combining the colors of the base and the overlay
    inputs, using the overlay as much as the 
    `stregth` parameter is indicating.

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
            uniform sampler2D base_texture;
            uniform sampler2D overlay_texture;
            uniform float mix_weight;  // 0.0 → only base, 1.0 → only overlay
            uniform float strength;  // 1.0 = full additive, 0.5 = subtle
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                vec4 base_color = texture(base_texture, v_uv);
                vec4 overlay_color = texture(overlay_texture, v_uv);

                vec4 result = base_color + overlay_color * strength;

                // Clamp to avoid overflow (values > 1.0)
                output_color = clamp(result, 0.0, 1.0);

                // Apply global mix intensity
                output_color = mix(base_color, output_color, mix_weight);
            }
            '''
        )
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'base_texture': 0,
            'overlay_texture': 1
        }
    
class AddBlenderGPU(_NodeBlenderGPU):
    """
    Blender to blend 2 textures by adding their values.

    This blender will increase the brightness by
    combining the colors of the base and the overlay
    inputs, using the overlay as much as the 
    `stregth` parameter is indicating.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _AddBlenderPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        base_input: moderngl.Texture,
        overlay_input: moderngl.Texture,
        output_size: Union[tuple[int, int], None] = None,
        mix_weight: float = 1.0,
        strength: float = 0.5,
    ) -> moderngl.Texture:
        """
        Blend the `base_input` with the `overlay_input` and
        get an output of the given `output_size` by using
        the also provided `mix_weight`.
        """
        return super().process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            mix_weight = mix_weight,
            strength = strength
        )