import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image

CANVAS_W = 512
CANVAS_H = 384


def scale_object(image_path, output_path, scale_pct, center_pct=50):
    """Scale an object PNG and place it on a transparent canvas.
    
    scale_pct: 100 = full size, 50 = half size
    center_pct: 50 = exact center, lower = higher in frame
    """
    obj = Image.open(image_path).convert("RGBA")
    
    # Calculate new size
    new_w = int(obj.width * scale_pct / 100)
    new_h = int(obj.height * scale_pct / 100)
    obj = obj.resize((new_w, new_h), Image.LANCZOS)
    
    # Create transparent canvas
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    
    # Position: centered horizontally, vertical based on center_pct
    x = (CANVAS_W - new_w) // 2
    y = int(CANVAS_H * center_pct / 100) - (new_h // 2)
    y = max(0, min(CANVAS_H - new_h, y))
    
    canvas.paste(obj, (x, y), obj)
    canvas.save(output_path)
    print(f"  Scaled to {scale_pct}% ({new_w}x{new_h}), placed at y={y}")


# Test with the existing dragon image
dragon = os.path.join(os.path.dirname(__file__), "output", "test_one_dragon.png")
if not os.path.exists(dragon):
    print(f"Image not found: {dragon}")
    sys.exit(1)

print("Testing object scaling with existing dragon image:\n")

for layer, scale in [(1, 100), (2, 90), (3, 80), (4, 70)]:
    center = 45 + (4 - layer) * 5  # Layer 1=60, Layer 2=55, Layer 3=50, Layer 4=45
    out = os.path.join(os.path.dirname(__file__), "output", f"scaled_layer{layer}.png")
    scale_object(dragon, out, scale, center)

print("\nDone! Check output/scaled_layer1-4.png")
print("Layer 1 = 100% (no shrink)")
print("Layer 2 = 90%")  
print("Layer 3 = 80%")
print("Layer 4 = 70%")
