from yta_editor_nodes_gpu.complex.abstract import _NodeComplexGPU
from yta_validation.parameter import ParameterValidator
from yta_video_opengl.context import OpenGLContext
from typing import Union

import moderngl


class DisplayOverAtNodeComplexGPU(_NodeComplexGPU):
    """
    The overlay input is placed in the scene with the
    given position, rotation and size, and then put as
    an overlay of the also given base input.

    Information:
    - The scene size is `(1920, 1080)`, so provide the
    `position` parameter according to it, where it is
    representing the center of the texture.
    - The `rotation` is in degrees, where `rotation=90`
    means rotating 90 degrees to the right.
    - The `size` parameter must be provided according to
    the previously mentioned scene size `(1920, 1080)`.

    This complex node is using the next other nodes:
    - `DisplacementWithRotationNodeCompositorGPU`
    - `AlphaBlenderGPU`
    """

    def __init__(
        self,
        opengl_context: Union[moderngl.Context, None]
    ):
        """
        Provide all the variables you want to be initialized
        as uniforms at the begining for the global OpenGL
        animation in the `**kwargs`.
        """
        ParameterValidator.validate_instance_of('opengl_context', opengl_context, moderngl.Context)

        self.context: moderngl.Context = (
            OpenGLContext().context
            if opengl_context is None else
            opengl_context
        )
        """
        The context of the OpenGL program.
        """

    def process(
        self,
        base_input: moderngl.Texture,
        overlay_input: moderngl.Texture,
        output_size: tuple[int, int] = (1920, 1080),
        position: tuple[int, int] = (1920 / 2, 1080 / 2),
        size: tuple[int, int] = (1920 / 2, 1080 / 2),
        rotation: int = 0
    ):
        """
        By default, the texture overlayed will be displayed in
        the center of the scene, with half of the scene size
        and no rotation.
        """
        from yta_editor_nodes_gpu.compositor import DisplacementWithRotationNodeCompositorGPU
        from yta_editor_nodes_gpu.blender import AlphaBlenderGPU

        displacement_node_processor = DisplacementWithRotationNodeCompositorGPU(
            opengl_context = self.context,
            # output_size = self._output_size
        )

        output = displacement_node_processor.process(
            #base_input = background_as_numpy,
            base_input = None,
            #overlay_input = background_as_numpy,
            overlay_input = overlay_input,
            # output_size = None,
            output_size = output_size,
            position = position,
            size = size,
            rotation = rotation
            #rotation = 0.785398 # 0.785398 = 45deg
        )

        if base_input is not None:
            #  TODO: Add just as an overlay
            blender = AlphaBlenderGPU(
                opengl_context = self.context,
                # TODO: Maybe accept it here
                # output_size = self._output_size
            )
            
            output = blender.process(
                # We don't need to care about the size because OpenGL
                # handles it
                base_input = base_input,
                overlay_input = output,
                output_size = output_size,
                mix_weight = 1.0,
                blend_strength = 1.0
            )

        return output