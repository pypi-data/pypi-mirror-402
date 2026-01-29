from yta_editor_nodes_gpu.processor.abstract import _NodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _ColorContrastPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to modify the color contrast
    of the textures we receive as input.

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
            uniform float factor;
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                vec4 color = texture(base_texture, v_uv);
                vec3 mean = vec3(0.5);
                color.rgb = (color.rgb - mean) * factor + mean;
                output_color = vec4(clamp(color.rgb, 0.0, 1.0), color.a);
            }
            '''
        )
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'base_texture': 0
        }
    
class ColorContrastNodeProcessorGPU(_NodeProcessorGPU):
    """
    A node to modify the color contrast of the
    textures that come as inputs.

    You multiply the distance to middle gray. Thus,
    the light areas become lighter and the dark areas
    darker. It's the simplest and most linear way to
    increase contrast without altering the overall
    brightness.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _ColorContrastPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        input: moderngl.Texture,
        output_size: Union[tuple[int, int], None] = None,
        factor: float = 1.5
    ) -> moderngl.Texture:
        """
        Process the `input` provided and get an output
        of the given `output_size` by using the `factor`
        provided.
        """
        return super().process(
            input = input,
            output_size = output_size,
            factor = factor
        )