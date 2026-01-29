from yta_editor_nodes_gpu.processor.video.abstract import _VideoNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


# TODO: I don't know if this is working
class _BreathingFramePipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    The frame but as if it was breathing.

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
            uniform float zoom;
            in vec2 v_uv;
            out vec4 output_color;
            // Use uniforms to be customizable

            void main() {
                // Dynamic zoom scaled with t
                float scale = 1.0 + zoom * sin(time * 2.0);
                vec2 center = vec2(0.5, 0.5);

                // Recalculate coords according to center
                vec2 uv = (v_uv - center) / scale + center;

                // Clamp to avoid artifacts
                uv = clamp(uv, 0.0, 1.0);

                output_color = texture(base_texture, uv);
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
    
class BreathingFrameVideoNodeProcessorGPU(_VideoNodeProcessorGPU):
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
            opengl_pipeline = _BreathingFramePipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        input: moderngl.Texture,
        t: float,
        output_size: Union[tuple[int, int], None] = None,
        zoom: float = 0.05
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
            zoom = zoom
        )