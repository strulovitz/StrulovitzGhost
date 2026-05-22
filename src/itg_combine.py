"""ITG Combine — Reduce N layers to 6 using pair-from-farthest combining.

Layer convention: L1 = closest to viewer (20cm), L6 = farthest (deep background).
Always combine from the FARTHEST end (end of list) — minimal parallax there.
Never combine the closest 4 layers (start of list) — strong parallax.
"""

import os, uuid
from PIL import Image


def create_empty_layer(size=(640, 640)):
    """Create a fully transparent RGBA PNG as a BytesIO."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    return img


def combine_two_layers(back_path, front_path, output_dir):
    """
    Combine two RGBA PNGs: back (farther) then front (closer) on top.
    Returns path to combined image.
    """
    back = Image.open(back_path).convert("RGBA")
    front = Image.open(front_path).convert("RGBA")

    # Resize to match if needed
    if back.size != front.size:
        front = front.resize(back.size, Image.LANCZOS)

    combined = Image.alpha_composite(back, front)
    combined_path = os.path.join(output_dir, f"combined_{uuid.uuid4().hex[:6]}.png")
    combined.save(combined_path, "PNG")
    return combined_path


def reduce_to_6_layers(z_ordered_paths, output_dir):
    """
    Given N RGBA layers sorted closest (index 0) to farthest (index N-1),
    reduce to exactly 6 layers.

    Rules:
    - If N == 6: return as-is
    - If N < 6: add empty transparent layers at FAR end (indices 6-N through 5)
    - If N > 6: pair-combine from the FARTHEST end until 6 remain

    Returns: list of exactly 6 paths (new combined/empty files if needed).
             Index 0 = closest (L1, 20cm), Index 5 = farthest (L6, background).
    """
    N = len(z_ordered_paths)
    os.makedirs(output_dir, exist_ok=True)

    if N == 6:
        return list(z_ordered_paths)

    if N < 6:
        # Real layers at closest positions, empty at farthest
        result = list(z_ordered_paths)
        for _ in range(6 - N):
            empty_path = os.path.join(output_dir, f"empty_{uuid.uuid4().hex[:6]}.png")
            create_empty_layer().save(empty_path, "PNG")
            result.append(empty_path)
        return result  # 6 items: closest real -> farthest empty

    # N > 6: Pair-combine from far end
    layers = list(z_ordered_paths)  # index 0 = closest

    while len(layers) > 6:
        # Combine the two FARTHEST (last two in list)
        combined = combine_two_layers(layers[-2], layers[-1], output_dir)
        layers = layers[:-2] + [combined]

    return layers  # Exactly 6: index 0 = closest (20cm), index 5 = farthest


# ─── Shell interface ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python itg_combine.py <output_dir> <layer1.png> <layer2.png> ... <layerN.png>")
        print("  Layers must be passed closest-first (L1 = closest to viewer).")
        print("  Output: 6 combined PNGs saved in <output_dir>/")
        sys.exit(1)

    output_dir = sys.argv[1]
    input_paths = sys.argv[2:]

    final = reduce_to_6_layers(input_paths, output_dir)

    print(f"Reduced {len(input_paths)} -> {len(final)} layers:")
    for i, p in enumerate(final):
        print(f"  Layer {i+1}: {os.path.basename(p)}")
