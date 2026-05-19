from PIL import Image, ImageDraw
import os


def make_placeholder_pngs():
    outdir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(outdir, exist_ok=True)

    colors = ["#1a1a4e", "#2d2d6e", "#3d3d8e", "#4d4dae", "#5d5dce", "#6d6dee"]
    labels = [
        "Layer6 Sky",
        "Layer5 Forest",
        "Layer4 Tiefling+Dragonborn",
        "Layer3 Dwarf+Halfling",
        "Layer2 Elf+Human",
        "Layer1 Framing",
    ]

    for i, (color, label) in enumerate(zip(colors, labels)):
        img = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 350, 250], fill=color, outline="white", width=3)
        draw.text((120, 140), label, fill="white")
        path = os.path.join(outdir, f"placeholder_layer{i+1}.png")
        img.save(path)
        print(f"  Created: {path}")

    print("6 placeholder PNGs created!")


if __name__ == "__main__":
    make_placeholder_pngs()
