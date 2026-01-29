from yta_editor_nodes_gpu.processor.video.transitions.abstract import _TransitionNodeProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


# TODO: This effect is not working according to
# the progress, you cannot use normal timing
class _BarsFallingTransitionPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to transition between the frames
    of 2 videos in which a set of bars fall with the
    first video to let the second one be seen.

    Extracted from here:
    - https://gl-transitions.com/editor/DoomScreenTransition

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
            uniform float progress; // 0.0 → start, 1.0 → end

            uniform int number_of_bars;           
            uniform float amplitude;        // Speed
            uniform float noise;            // Extra noise [0.0, 1.0]
            uniform float frequency;        // Wave frequency
            uniform float drip_scale;       // Falling from center

            in vec2 v_uv;
            out vec4 output_color;

            // pseudo-random from integer
            float rand(int num) {
                return fract(mod(float(num) * 67123.313, 12.0) * sin(float(num) * 10.3) * cos(float(num)));
            }

            // Wave for vertical distortion
            float wave(int num) {
                float fn = float(num) * frequency * 0.1 * float(number_of_bars);
                return cos(fn * 0.5) * cos(fn * 0.13) * sin((fn + 10.0) * 0.3) / 2.0 + 0.5;
            }

            // Vertical curve to borders
            float drip(int num) {
                return sin(float(num) / float(number_of_bars - 1) * 3.141592) * drip_scale;
            }

            // Displacement for a bar
            float pos(int num) {
                float w = wave(num);
                float r = rand(num);
                float base = (noise == 0.0) ? w : mix(w, r, noise);
                return base + ((drip_scale == 0.0) ? 0.0 : drip(num));
            }

            void main() {
                int bar = int(v_uv.x * float(number_of_bars));

                float scale = 1.0 + pos(bar) * amplitude;
                float phase = progress * scale;
                float pos_y = v_uv.y;

                vec2 p;
                vec4 color;

                if (phase + pos_y < 1.0) {
                    // Frame A is visible
                    p = vec2(v_uv.x, v_uv.y + mix(0.0, 1.0, phase));
                    color = texture(first_texture, p);
                } else {
                    // Frame B is visible
                    color = texture(second_texture, v_uv);
                }

                output_color = color;
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
    
class BarsFallingTransitionNodeProcessorGPU(_TransitionNodeProcessorGPU):
    """
    A transition between the frames of 2 videos in
    which the frames are mixed by generating a
    decreasing from the middle to end disappearing.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None,
        number_of_bars: int = 30,
        amplitude: float = 2.0,
        noise: float = 0.1, # [0.0, 1.0]
        frequency: float = 0.5,
        drip_scale: float = 0.5,
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _BarsFallingTransitionPipelineGPU(
                opengl_context = opengl_context
            ),
            number_of_bars = number_of_bars,
            amplitude = amplitude,
            noise = noise,
            frequency = frequency,
            drip_scale = drip_scale,
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