"""Combine multiple RGBA PNGs into a single composite image.
Layers are composited back-to-front (first = bottom/background, last = top/foreground).
Usage: python combine.py output.png layer6.png layer5.png layer4.png layer3.png layer2.png layer1.png
"""

import sys
from PIL import Image


def combine_layers(layer_paths, output_path):
    """Stack RGBA PNGs back-to-front into a single composite.
    
    Args:
        layer_paths: list of file paths, first = backmost layer, last = frontmost
        output_path: where to save the composite RGBA PNG
    """
    if not layer_paths:
        raise ValueError("No layers provided")

    # Start with the backmost layer
    composite = Image.open(layer_paths[0]).convert("RGBA")

    # Stack each subsequent layer on top
    for path in layer_paths[1:]:
        overlay = Image.open(path).convert("RGBA")
        composite = Image.alpha_composite(composite, overlay)

    composite.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine.py <output.png> <layer_back.png> <layer_mid.png> ... <layer_front.png>")
        print("Example: python combine.py scene.png layer6.png layer5.png layer4.png layer3.png layer2.png layer1.png")
        sys.exit(1)

    out = sys.argv[1]
    paths = sys.argv[2:]
    result = combine_layers(paths, out)
    print(f"Combined {len(paths)} layers -> {result}")
