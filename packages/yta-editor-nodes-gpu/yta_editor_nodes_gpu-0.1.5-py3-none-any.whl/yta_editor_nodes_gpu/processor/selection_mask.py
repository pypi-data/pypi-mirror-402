from yta_editor_nodes_gpu.processor.abstract import _SelectionMaskProcessorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from typing import Union

import moderngl


class _SelectionMaskPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    A OpenGL pipeline to to use a mask selection (from
    which we will read the red color to determine if
    the pixel must be applied or not) to apply the
    `processed_texture` on the `original_texture`.

    If the selection mask is completely full, the
    result will be the `processed_texture`. If it is
    completely empty, the `original_texture`.

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

            uniform sampler2D original_texture;
            uniform sampler2D processed_texture;
            // White = apply, black = ignore
            uniform sampler2D selection_mask_texture;
            in vec2 v_uv;
            out vec4 output_color;

            void main() {
                vec4 original_color = texture(original_texture, v_uv);
                vec4 processed_color = texture(processed_texture, v_uv);
                // We use the red as the value
                float mask = texture(selection_mask_texture, v_uv).r; 

                output_color = mix(original_color, processed_color, mask);
            }
            '''
        )
    
    @property
    def _textures_expected(
        self
    ) -> dict:
        return {
            'original_texture': 0,
            'processed_texture': 1,
            'selection_mask_texture': 2
        }
    
class SelectionMaskNodeProcessorGPU(_SelectionMaskProcessorGPU):
    """
    Class to use a mask selection (from which we will
    read the red color to determine if the pixel must
    be applied or not) to apply the `processed_texture`
    on the `original_texture`.

    If the selection mask is completely full, the
    result will be the `processed_texture`.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _SelectionMaskPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        original_input: moderngl.Texture,
        processed_input: moderngl.Texture,
        selection_mask_input: moderngl.Texture,
        output_size: Union[tuple[int, int], None] = None
    ) -> moderngl.Texture:
        """
        Process the `original_input`, `processed_input` and
        `selection_mask_input` provided and get an output of
        the given `output_size`.
        """
        return super().process(
            original_input = original_input,
            processed_input = processed_input,
            selection_mask_input = selection_mask_input,
            output_size = output_size,
        )