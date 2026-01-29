from yta_editor_nodes_gpu.blender.abstract import _NodeBlenderGPU
from yta_editor_nodes_gpu.blender.utils import _validate_inputs_and_mix_weights
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _MixBlenderPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    Class to represent a blender that uses GPU to
    blend the inputs. This blender will process the
    inputs as textures and will generate also a
    texture as the output.

    Blender results can be chained and the result
    from one node can be applied on another node.

    This blender is able to work acting as an
    opacity blender, but will be used as the base
    of the classes that we will implement actually.

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
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                vec4 base_color = texture(base_texture, v_uv);
                vec4 overlay_color = texture(overlay_texture, v_uv);

                // Apply global mix intensity
                output_color = mix(base_color, overlay_color, mix_weight);
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
    
class MixBlenderGPU(_NodeBlenderGPU):
    """
    Class to represent a blender that uses GPU to
    blend the inputs. This blender will process the
    inputs as textures and will generate also a
    texture as the output.

    Blender results can be chained and the result
    from one node can be applied on another node.

    This blender is able to work acting as an
    opacity blender, but will be used as the base
    of the classes that we will implement actually.

    This pipeline is specific and unique for its the
    Node with the same name.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _MixBlenderPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        base_input: moderngl.Texture,
        overlay_input: moderngl.Texture,
        output_size: Union[tuple[int, int], None] = None,
        mix_weight: float = 1.0
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
            mix_weight = mix_weight
        )
    
    # TODO: This method can change according to the way
    # we need to process the inputs, that could be
    # different than by pairs
    def process_multiple_inputs(
        self,
        inputs: list[moderngl.Texture],
        mix_weights: Union[list[float], float] = 1.0,
        output_size: Union[tuple[int, int], None] = None,
    ) -> moderngl.Texture:
        """
        Blend all the `inputs` provided, one after another,
        applying the `mix_weights` provided, and forcing the
        result to the `dtype` if provided.

        The `mix_weights` can be a single float value, that 
        will be used for all the mixings, or a list of as
        many float values as `inputs` received, to be 
        applied individually to each mixing.
        """
        _validate_inputs_and_mix_weights(
            inputs = inputs,
            mix_weights = mix_weights
        )
        
        # We process all the 'inputs' as 'base' and 'overlay'
        # and accumulate the result

        # Use the first one as the base
        output = inputs[0]

        # TODO: How do we handle the additional parameters that
        # could be an array? Maybe if it is an array, check that
        # the number of elements is the same as the number of
        # inputs, and if a single value just use it...

        for i in range(1, len(inputs)):
            overlay_input = inputs[i]
            mix_weight = mix_weights[i]

            output = self.process(
                base_input = output,
                overlay_input = overlay_input,
                output_size = output_size,
                mix_weight = mix_weight,
            )

        return output