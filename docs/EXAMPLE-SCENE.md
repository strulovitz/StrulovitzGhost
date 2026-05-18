# Example Scene: D&D Night Camp 🌙🏕️

This is a fully worked example showing how a Dungeon Master's text description gets broken into depth layers for the Strulovitz Ghost 6-layer display.

---

## The Scene (DM's Text Description)

> The group has stopped to make camp in a peaceful moon-lit clearing in the forest. The night sky is clear, filled with stars and a bright full moon. In the far distance, snow-capped mountains rise on the horizon. A magical forest of ancient oak trees surrounds the clearing. The party is spread out across the campsite, settling in for the night. A small campfire crackles in the center, roasting a wild pig from the day's hunt. The viewer is peeping into the clearing from the edge of the forest — branches frame the scene, and an owl watches silently from a nearby branch. A curious rabbit sits on a tree root, its back to us, looking toward the noisy group.

---

## Layer Breakdown (Farthest → Closest)

### Layer 6 — Sky & Moon 🌌 (Farthest from viewer, ~2 meters away)

**What it contains:**
- Clear night sky filled with stars
- A bright, glowing full moon
- Subtle clouds near the moon

**Everything else:** TRANSPARENT

**Purpose:** Establishes the deepest background — infinite distance. The moon provides the light source for the entire scene.

---

### Layer 5 — Far Mountains 🏔️

**What it contains:**
- Snow-capped mountain peaks on the horizon
- Dark mountain silhouettes against the night sky
- Misty haze at the base of the mountains

**Everything else:** TRANSPARENT

**Purpose:** Creates the far background — establishes the wilderness setting. The mountains sit behind the forest and give scale to the world.

---

### Layer 4 — The Magical Forest 🌳✨

**What it contains:**
- Ancient, large oak trees — thick trunks, sprawling branches
- Magical atmosphere — perhaps subtle glowing motes or runes on some trees
- The tree line forming the edge of the clearing
- Dark shadows between trees suggesting deeper forest

**Everything else:** TRANSPARENT

**Purpose:** This is the mid-background. The forest frames the entire scene and establishes the "clearing" setting. The magical touches hint that this is a fantasy world.

---

### Layer 3 — Tiefling Fighter & Dragonborn Wizard 🗡️📖

**What it contains:**
- **Tiefling Fighter Girl** — sitting on a medium-sized rounded rock, sharpening her sword with a whetstone. Her horns and tail are visible. She looks focused and serious.
- **Dragonborn Wizard Guy** — sitting on his own medium rounded rock nearby, hunched over his magic spellbook, memorizing spells. His dragon-like scales catch the moonlight faintly.
- Medium-distance flower patches scattered over soft green grass
- The rocks they sit on

**Everything else:** TRANSPARENT

**Purpose:** First layer containing characters. These two are at a medium distance from the viewer — not in the immediate foreground, not in the far back.

---

### Layer 2 — Dwarf Cleric & Halfling Thief + Campfire 🔥🐗

**What it contains:**
- **Dwarf Cleric Guy** — standing, gesturing angrily/enthusiastically, his armor and holy symbol visible
- **Halfling Thief Guy** — standing opposite the Dwarf, also gesturing, looking defensive but mischievous
- Between them: a small campfire with flames and embers
- Over the fire: a wild pig roasting on a spit (the group hunted it earlier)
- Closer beautiful flower patches over closer soft green grass
- The ground around the campfire (bare earth from foot traffic)

**Everything else:** TRANSPARENT

**Purpose:** The mid-foreground. These two characters are closer to us and in the middle of an argument. The campfire is the central gathering point. The roasting pig adds detail and hints at the group's recent activity.

---

### Layer 1 — Elf Paladin & Human Druid 🌿👯‍♀️

**What it contains:**
- **Elf Paladin Girl** — sitting on a fallen tree log trunk, turned away from us (her back to the viewer), gossiping and laughing with the Druid
- **Human Druid Girl** — also sitting on the same fallen tree trunk, back to the viewer, laughing and leaning toward the Elf
- The fallen tree log trunk (textured bark, moss)
- Their backpacks and blankets neatly packed on the tree beside them

**Everything else:** TRANSPARENT

**Purpose:** The closest character layer. These two are right near the viewer, with their backs to us — this makes us feel like we're standing right behind them.

---

### Layer 0 — Foreground Framing 🦉🐇 (Closest to viewer, ~20 cm away)

**What it contains:**
- Very close tree branch tips entering from the sides and top edges (like a natural frame)
- On one branch: an owl sitting silently, watching the scene
- A curious rabbit sitting on a thick tree root at ground level, its back to us, looking toward the noisy group
- The tree root with bark texture

**Everything else:** TRANSPARENT

**Purpose:** The closest possible elements. These frame the scene from the edges (not blocking the main view) and provide the ultimate depth cue. The viewer is "peeping" from the forest into the clearing. The rabbit and owl add life and reinforce the idea that the group is being watched from the woods.

---

## Note on Layer Count ⚠️

The physical Strulovitz Ghost setup has **6 layers** (3 monitors × 2 layers each), but this example describes **7 layers** (6 scene layers + 1 foreground framing layer). This will be resolved during implementation — options include:

- Combine Layer 1 and Layer 0 into a single PNG (characters + foreground framing on the same layer)
- Adjust the physical setup to accommodate more layers
- Assign the foreground framing to share Layer 1 on the closest monitor

This is a planning consideration for the implementation phase.

---

## The Characters (Full Reference)

These are the **6 player characters** in our example D&D group. They appear across Layers 1–3 in this scene.

| # | Species | Class | Gender | Layer | Activity in This Scene |
|---|---------|------|--------|-------|------------------------|
| 1 | Tiefling | Fighter | Girl | 3 | Sharpening her sword on a rock |
| 2 | Dragonborn | Wizard | Guy | 3 | Memorizing spells from his magic book |
| 3 | Dwarf | Cleric | Guy | 2 | Arguing over the campfire |
| 4 | Halfling | Thief | Guy | 2 | Arguing over the campfire |
| 5 | Elf | Paladin | Girl | 1 | Gossiping and laughing (back to viewer) |
| 6 | Human | Druid | Girl | 1 | Gossiping and laughing (back to viewer) |

---

## Summary: Depth Map

```
VIEWER 👁️
  │
  │  20 cm  ┃ Layer 0: Branches, owl, rabbit (framing)
  │         ┃ Layer 1: Elf Paladin + Human Druid (on tree trunk)
  │         ┃ Layer 2: Dwarf Cleric + Halfling Thief + campfire
  │         ┃ Layer 3: Tiefling Fighter + Dragonborn Wizard (on rocks)
  │         ┃ Layer 4: Magical forest of oak trees
  │         ┃ Layer 5: Far mountains (snow-capped)
  │   2 m   ┃ Layer 6: Night sky, stars, moon
  │
  ▼  INFINITY
```
