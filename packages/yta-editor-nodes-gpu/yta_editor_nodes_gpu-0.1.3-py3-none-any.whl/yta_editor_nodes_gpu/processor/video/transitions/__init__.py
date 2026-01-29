from yta_editor_nodes_gpu.processor.video.transitions.alphapedia_mask import AlphaPediaMaskTransitionNodeProcessorGPU
from yta_editor_nodes_gpu.processor.video.transitions.bars_falling import BarsFallingTransitionNodeProcessorGPU
from yta_editor_nodes_gpu.processor.video.transitions.circle_closing import CircleClosingTransitionNodeProcessorGPU
from yta_editor_nodes_gpu.processor.video.transitions.circle_opening import CircleOpeningTransitionNodeProcessorGPU
from yta_editor_nodes_gpu.processor.video.transitions.crossfade import CrossfadeTransitionNodeProcessorGPU
from yta_editor_nodes_gpu.processor.video.transitions.distorted_crossfade import DistortedCrossfadeTransitionNodeProcessorGPU
from yta_editor_nodes_gpu.processor.video.transitions.slide import SlideTransitionNodeProcessorGPU


__all__ = [
    'AlphaPediaMaskTransitionNodeProcessorGPU',
    'BarsFallingTransitionNodeProcessorGPU',
    'CircleClosingTransitionNodeProcessorGPU',
    'CircleOpeningTransitionNodeProcessorGPU',
    'CrossfadeTransitionNodeProcessorGPU',
    'DistortedCrossfadeTransitionNodeProcessorGPU',
    'SlideTransitionNodeProcessorGPU'
]


"""
Note for the developer:

Here below you have a shader that allows you
to create more slide transitions (vertical,
diagonal) but have to be refactored because
the mixing part is not working properly
according to the position. The code was made
for an horizontal slide but has to be adapted
to the other movements.

Code here below:

#version 330

// FRAGMENT SHADER — Slide horizontal
uniform sampler2D texA;
uniform sampler2D texB;
uniform float progress;     // 0.0 → full A, 1.0 → full B

in vec2 frag_uv;
out vec4 frag_color;

void main() {
    // Horizontal version (right to left)
    vec2 uvA = frag_uv + vec2(-progress, 0.0);
    vec2 uvB = frag_uv + vec2(1.0 - progress, 0.0);
    
    // Horizontal version (left to right)
    //vec2 uvA = frag_uv + vec2(progress, 0.0);
    //vec2 uvB = frag_uv + vec2(-1.0 + progress, 0.0);

    // Vertical version (top to bottom)
    // TODO: We need to adjust the color mixin
    // to make it fit the type of transition
    //vec2 uvA = frag_uv + vec2(0.0, -progress);
    //vec2 uvB = frag_uv + vec2(0.0, 1.0 - progress);

    // Diagonal version (top left to bottom right)
    //vec2 uvA = frag_uv + vec2(-progress, -progress);
    //vec2 uvB = frag_uv + vec2(1.0 - progress, 1.0 - progress);

    vec4 colorA = texture(texA, uvA);
    vec4 colorB = texture(texB, uvB);

    if (uvA.x < 0.0) {
        frag_color = colorB;
    } else if (uvB.x > 1.0) {
        frag_color = colorA;
    } else {
        // A and B frames are shown at the same time
        frag_color = mix(colorA, colorB, progress);
    }
}
"""