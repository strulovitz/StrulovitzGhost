import sys
import traceback
sys.path.insert(0, r"C:\Users\nir_s\StrulovitzGhost\src")

try:
    from generator import generate_diffusers
    result = generate_diffusers(
        "A cute dragon, cartoon style",
        r"C:\Users\nir_s\StrulovitzGhost\src\output\test_dragon4.png",
        width=256, height=256, num_steps=4,
    )
    print("SUCCESS!" if result else "FAILED")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
