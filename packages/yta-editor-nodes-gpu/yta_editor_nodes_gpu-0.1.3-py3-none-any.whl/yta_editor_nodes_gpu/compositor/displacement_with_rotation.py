from yta_editor_nodes_gpu.compositor.abstract import _NodeCompositorGPU
from yta_video_opengl.new.pipeline import _OpenGLPipeline
from yta_validation.parameter import ParameterValidator
from typing import Union

import moderngl


class _DisplacementWithRotationPipelineGPU(_OpenGLPipeline):
    """
    *For internal use only*

    Class to represent a node processor that uses GPU
    to composite the input into the scene, by rotating,
    positioning it, etc.

    This pipeline is specific and unique for its the
    Node with the same name.
    """

    @property
    def vertex_shader(
        self
    ) -> str:
        """
        The code of the vertex shader. This is, by default,
        a rectangle made by 2 triangles that will be placed
        in the specific position, with the size provided and
        with the also given rotation.
        """
        return (
            '''
            #version 330

            in vec2 in_vert;        // Quad vertices [-1.0, 1.0]
            in vec2 in_texcoord;    // UV Coordinates: (0, 0) a (1, 1)
            out vec2 v_uv;

            uniform vec2 position;  // Center of texture
            uniform vec2 size;      // Size of texture (w, h)
            uniform float rotation; // Rotation (in degrees)

            // Resolution of the viewport
            // TODO: Turn this into a uniform with default value
            const vec2 resolution = vec2(1920.0, 1080.0);

            vec2 rotate_around_center(vec2 p, float rotation) {
                float radians = radians(rotation);
                float s = sin(radians);
                float c = cos(radians);
                mat2 rot = mat2(c, -s, s, c);
                return rot * p;
            }

            void main() {
                // Local coordinates but in [-0.5, 0.5]
                vec2 local = in_vert * 0.5;

                vec2 scaled = local * size;
                vec2 rotated = rotate_around_center(scaled, rotation);
                vec2 pos_pixels = position + rotated;

                // Pixels to normalized coordinates [-1.0, 1.0]
                vec2 ndc = (pos_pixels / resolution) * 2.0 - 1.0;

                gl_Position = vec4(ndc, 0.0, 1.0);
                v_uv = in_texcoord;
            }
            '''
        )
    
    @property
    def fragment_shader(
        self
    ) -> str:
        return (
            '''
            #version 330
            in vec2 v_uv;
            out vec4 output_color;
            uniform sampler2D base_texture;
            uniform sampler2D overlay_texture;
            uniform bool do_use_transparent_base_texture;

            void main() {
                vec4 base_color;

                if (do_use_transparent_base_texture) {
                    base_color = vec4(0.0, 0.0, 0.0, 0.0);
                } else {
                    //base_color = vec4(1.0, 1.0, 1.0, 1.0);
                    base_color = texture(base_texture, v_uv);
                }

                vec4 overlay_color = texture(overlay_texture, v_uv);
                output_color = mix(base_color, overlay_color, overlay_color.a);
                //output_color = vec4(v_uv, 0.0, 1.0);
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

class DisplacementWithRotationNodeCompositorGPU(_NodeCompositorGPU):
    """
    Class to represent a node processor that uses GPU
    to composite the input into the scene, by rotating,
    positioning it, etc.
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None] = None
    ):
        # TODO: Validate context (?)
        super().__init__(
            opengl_pipeline = _DisplacementWithRotationPipelineGPU(
                opengl_context = opengl_context
            )
        )

    def process(
        self,
        base_input: Union[moderngl.Texture, None],
        overlay_input: moderngl.Texture,
        # TODO: We need the value as pixels in (1920, 1080)
        position: tuple[int, int],
        size: tuple[int, int],
        rotation: int,
        output_size: Union[tuple[int, int], None] = None,
    ) -> moderngl.Texture:
        """
        Mix the `base_input` with the `overlay_input`
        based on the `progress` given. The `base_input`
        can be None if we just want to position the
        `overlay_input` in a transparent background.

        We use and return textures to maintain the
        process in GPU and optimize it.
        """
        ParameterValidator.validate_instance_of('base_input', base_input, moderngl.Texture)
        ParameterValidator.validate_mandatory_instance_of('overlay_input', overlay_input, moderngl.Texture)

        do_use_transparent_base_texture = base_input is None

        textures_map = {}

        if base_input is not None:
            # TODO: The size will be obtained from the first texture
            # dynamically, but if we don't provide the base texture,
            # it will be created as a completely transparent one,
            # that doesn't have any size in the 'textures_map' var
            textures_map['base_texture'] = base_input
        
        textures_map = textures_map | {
            # TODO: I think the 'base_input' should be forced to
            # be a completely transparent texture here
            'overlay_texture': overlay_input
        }

        return self._process_common(
            textures_map = textures_map,
            output_size = output_size,
            position = position,
            size = size,
            rotation = rotation,
            do_use_transparent_base_texture = do_use_transparent_base_texture
        )