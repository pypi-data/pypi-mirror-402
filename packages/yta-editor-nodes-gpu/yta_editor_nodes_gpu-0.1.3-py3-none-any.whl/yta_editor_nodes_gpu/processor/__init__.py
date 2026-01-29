"""
The nodes that modify inputs by using static parameters
and not 't' time moments, with GPU.
"""
from yta_editor_nodes_gpu.processor.black_and_white import BlackAndWhiteNodeProcessorGPU
from yta_editor_nodes_gpu.processor.brightness import BrightnessNodeProcessorGPU
from yta_editor_nodes_gpu.processor.color_contrast import ColorContrastNodeProcessorGPU
from yta_editor_nodes_gpu.processor.selection_mask import SelectionMaskNodeProcessorGPU


__all__ = [
    'BlackAndWhiteNodeProcessorGPU',
    'BrightnessNodeProcessorGPU',
    'ColorContrastNodeProcessorGPU',
    'SelectionMaskNodeProcessorGPU'
]
    




