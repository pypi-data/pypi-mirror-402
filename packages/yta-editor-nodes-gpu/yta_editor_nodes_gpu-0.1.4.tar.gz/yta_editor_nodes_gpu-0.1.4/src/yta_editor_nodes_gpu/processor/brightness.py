from yta_editor_nodes_gpu.processor.abstract import _NodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _BrightnessPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to modify the brightness of the
    textures we receive as input by multiplying the
    color by a factor.

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
            uniform float factor; // 1.0 = no change, >1.0 lighter, <1.0 darker
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                vec4 color = texture(base_texture, v_uv);
                color.rgb *= factor;
                output_color = color;
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
    
class BrightnessNodeProcessorGPU(_NodeProcessorGPU):
    """
    A node to modify the brightness of the textures
    we receive as input by multiplying the color by a
    factor.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _BrightnessPipelineGPU(
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
        given.
        """
        return super().process(
            input = input,
            output_size = output_size,
            factor = factor
        )