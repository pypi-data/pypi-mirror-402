from yta_video_opengl.new.opengl_nodes import _SingleTextureOpenGLNode, _OriginalProcessedSelectionOpenGLNode


class _NodeProcessorGPU(_SingleTextureOpenGLNode):
    """
    *For internal use only*

    Class to represent a node processor that uses GPU
    to transform a single input (a single texture).

    The shader is using one single input textured called
    `base_texture`.
    """

    pass

class _SelectionMaskProcessorGPU(_OriginalProcessedSelectionOpenGLNode):
    """
    *For internal use only*

    Class to represent a node that uses GPU to mix an
    original texture with a processed one, based on a
    mask texture that is also pased as input.

    The shader is using three inputs, called
    `original_texture`, `processed_texture` and
    `selection_mask_texture`.
    """

    pass