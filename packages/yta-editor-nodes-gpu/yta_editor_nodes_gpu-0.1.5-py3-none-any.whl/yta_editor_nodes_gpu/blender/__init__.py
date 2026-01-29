"""
This entire module is working with OpenGL.

We don't name it 'blend' instead of 'process' because
the GPU classes have the 'process' name due to the
inheritance from OpenGL classes, and we want to avoid
misunderstandings.

(!) IMPORTANT:
In all our blenders we need to include a uniform
called `mix_weight` to determine the percentage of 
effect we want to apply to the output result:
- `uniform float mix_weight;  // 0.0 → only base, 1.0 → only overlay`
- `output_color = mix(base_color, overlay_color, mix_weight);`
"""
from yta_editor_nodes_gpu.blender.add import AddBlenderGPU
from yta_editor_nodes_gpu.blender.alpha import AlphaBlenderGPU
from yta_editor_nodes_gpu.blender.mix import MixBlenderGPU


__all__ = [
    'AddBlenderGPU',
    'AlphaBlenderGPU',
    'MixBlenderGPU'
]
