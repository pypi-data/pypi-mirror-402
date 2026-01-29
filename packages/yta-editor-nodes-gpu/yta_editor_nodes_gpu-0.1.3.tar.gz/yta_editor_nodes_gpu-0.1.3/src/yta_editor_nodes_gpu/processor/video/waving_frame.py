from yta_editor_nodes_gpu.processor.video.abstract import _VideoNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _WavingFramePipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    The video frames that are transformed into a wave.

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
            uniform float time;
            uniform float amplitude;
            uniform float frequency;
            uniform float speed;
            uniform bool do_use_transparent_pixels;
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                float wave = sin(v_uv.x * frequency + time * speed) * amplitude;
                vec2 uv = vec2(v_uv.x, v_uv.y + wave);

                // Si el UV se sale del rango, devolvemos transparencia
                if ((uv.y < 0.0 || uv.y > 1.0) && do_use_transparent_pixels) {
                    output_color = vec4(0.0, 0.0, 0.0, 0.0);
                } else {
                    output_color = texture(base_texture, uv);
                }
            }
            '''
        )
    
    # TODO: This below doesn't use transparent pixels but
    # the other pixels of the image instead
    """
    void main() {
        float wave = sin(v_uv.x * frequency + time * speed) * amplitude;
        vec2 uv = vec2(v_uv.x, v_uv.y + wave);
        output_color = texture(base_texture, uv);
    }
    """
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'base_texture': 0
        }
    
class WavingFrameVideoNodeProcessorGPU(_VideoNodeProcessorGPU):
    """
    A node to modify a video to make the frames be
    transformed into a wave.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None,
        amplitude: float = 0.05,
        frequency: float = 10.0,
        speed: float = 2.0,
        do_use_transparent_pixels: bool = False
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _WavingFramePipelineGPU(
                opengl_context = opengl_context
            ),
            amplitude = amplitude,
            frequency = frequency,
            speed = speed,
            do_use_transparent_pixels = do_use_transparent_pixels
        )

    def process(
        self,
        input: moderngl.Texture,
        t: float,
        output_size: Union[tuple[int, int], None] = None
        # We do not accept 'uniforms' because changing
        # them here could break it all
    ) -> moderngl.Texture:
        """
        Process the `input` provided and get an output of
        the given `output_size` and for the `t` time
        moment provided.
        """
        return super().process(
            input = input,
            t = t,
            output_size = output_size,
        )