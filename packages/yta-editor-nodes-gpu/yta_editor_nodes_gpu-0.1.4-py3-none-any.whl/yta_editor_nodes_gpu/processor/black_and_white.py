from yta_editor_nodes_gpu.processor.abstract import _NodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _BlackAndWhitePipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to modify the color of the
    textures we receive as input by transforming
    them into black and white outputs.

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
                // Luminance Rec.709
                float gray = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
                output_color = vec4(vec3(gray), color.a);
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
    
class BlackAndWhiteNodeProcessorGPU(_NodeProcessorGPU):
    """
    A node to modify the color of the textures we
    receive as input by transforming them into a black
    and white outputs.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _BlackAndWhitePipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        input: moderngl.Texture,
        output_size: Union[tuple[int, int], None] = None
    ) -> moderngl.Texture:
        """
        Process the `input` provided and get an output
        of the given `output_size` by using the
        `**dynamic_uniforms` if needed.
        """
        return super().process(
            input = input,
            output_size = output_size,
        )