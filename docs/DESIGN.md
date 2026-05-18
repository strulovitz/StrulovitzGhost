# Strulovitz Ghost — Design Document 👻

## Inspiration: Pepper's Ghost

[Pepper's Ghost](https://en.wikipedia.org/wiki/Pepper%27s_ghost) is a classic illusion technique using a sheet of glass (or transparent plastic) at a 45° angle. The viewer sees both the reflection from the glass and whatever is behind it, creating a ghostly, semi-transparent apparition.

**Strulovitz Ghost extends this idea to multiple layers** — not just one, but six layers arranged in depth, each one behind the other.

---

## The Physical Setup (DIY — Done by the User)

### Monitors

- **3 gaming monitors** are laid flat on a table, side by side in a line (like 3 floor tiles)
- Each monitor faces upward (screen towards the ceiling)
- The user's gaming PC must support at least 3 monitor outputs (standard on modern NVIDIA/AMD cards)

### Reflective Layers

- Each layer is made from a **transparent CD or DVD plastic case**, opened and positioned at a **45° angle**
- The case is fixed in place using a **toothpick and adhesive tape**
- **2 layers per monitor**:
  - One on the **near side** of the monitor (closer to the user)
  - One on the **far side** of the monitor (farther from the user)
  - Both layers face the same direction

### Total Configuration

| Monitor | Layer Position | Layer # |
|---------|---------------|---------|
| Monitor 1 (closest to user) | Near side | Layer 1 |
| Monitor 1 (closest to user) | Far side  | Layer 2 |
| Monitor 2 (middle)          | Near side | Layer 3 |
| Monitor 2 (middle)          | Far side  | Layer 4 |
| Monitor 3 (farthest)        | Near side | Layer 5 |
| Monitor 3 (farthest)        | Far side  | Layer 6 |

**Total: 3 monitors × 2 layers = 6 layers**

---

## The Viewing Experience

The user sits at the **head of the table**, looking through all 6 layers stacked in depth.

- **Layer 1** (closest): ~20 cm from the user's eyes — appears very near
- **Layer 6** (farthest): ~2 meters from the user's eyes — appears very far
- Each layer is **half-transparent**, so the user can see through it to all layers behind it

The result is a scene with **real physical depth** — not simulated on a flat screen, but actually occupying 3D space between 20 cm and 2 meters from the viewer.

---

## Software Role (What We Build Here)

The software's job is to **calculate and render the correct image for each of the 6 layers**. Each monitor receives two images (one for its near layer, one for its far layer). The images must account for:

- The 45° reflection angle
- The transparency of each layer
- The depth position of each layer
- What the user should see through each layer at their specific viewing angle

---

## Future Stages (Planned)

| Stage | Description |
|-------|-------------|
| **Stage 1** | Static images — render a single frame across all 6 layers |
| **Stage 2** | Real-time rendering — dynamic graphics that update per frame |
| **Stage 3** | Game engine integration — hook into existing fantasy games |

---

## Project Structure

```
StrulovitzGhost/
├── README.md           # Project overview
├── docs/
│   └── DESIGN.md       # This document — full design details
├── src/                # Source code (Python)
│   └── ...
└── ...
```
