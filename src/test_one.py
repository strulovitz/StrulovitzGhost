import sys, os
sys.path.insert(0, os.path.dirname(__file__))

def progress(msg, pct):
    print(f"  [{pct}%] {msg}")

print("One generation test with timing estimate + progress...\n")

from generator import generate_diffusers

result = generate_diffusers(
    "A cute small dragon, cartoon style, centered",
    os.path.join(os.path.dirname(__file__), "output", "test_one_dragon.png"),
    width=512, height=384,
    num_steps=15,
    remove_bg=True,
    progress_callback=progress,
)

print(f"\nResult: {'SUCCESS' if result else 'FAILED'}")
