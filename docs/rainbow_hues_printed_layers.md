# 🌈 Rainbow Hues on Semi-Transparent Printed Layers

**Problem:** When viewing the Silver Warrior scene in physical half-transparent plastic layers (Pepper's Ghost display), rainbow-colored hues appear that are NOT visible when viewing the same layer images on a digital screen.

---

## Answer: Thin-Film Interference

The rainbow hues are caused by **thin-film interference** — the same optical phenomenon behind oil slicks on water, soap bubbles, and iridescent coatings.

### Why Printed Layers Show Rainbows (But Screens Don't)

When you look at a digital screen, you are looking at an **emissive light source**. The screen dictates exactly which wavelengths of light reach your eyes, mixed into pixels of red, green, and blue.

A semi-transparent printed layer (like a clear varnish, UV cure, or glossy laminate) behaves differently because it relies on ambient white light reflection:

1. **The Nanometer Trap:** A semi-transparent printed layer is incredibly thin, often close to the wavelength of visible light (400 to 700 nanometers).

2. **The Split Light Wave:** When external light hits this layer, some light reflects off the top surface of the print. The rest passes through the layer and reflects off the bottom surface (the underlying paper or ink).

3. **Constructive Interference:** Because the layer is microscopic, these two reflections bounce back almost perfectly in sync. If the thickness of the printed layer matches a specific wavelength of light, those light waves reinforce each other (constructive interference) and blast a vivid, metallic color to your eye.

4. **The Fluid Rainbow:** Print layers are rarely perfectly uniform; their thickness varies by tiny fractions of a nanometer across the page. As the thickness shifts, the boosted color shifts, creating a sweeping rainbow effect across the material.

### Additional Contributing Factors in This Setup

- **Chroma-key edge fringing:** The green-to-alpha transition has sub-pixel color bleed invisible on screen but amplified when light passes through physical plastic.
- **Polarization:** Monitors emit polarized light. The 6 stacked plastic layers can act as polarizing filters at certain angles (Monitor #3 already has known polarization issues).
- **Printer/plastic artifacts:** Micro-variations in the printed plastic surface diffract light differently than pixels on a screen.

### How This Applies to Pepper's Ghost Displays

A Pepper's Ghost display relies on a clear pane of glass or a polymer film placed at a 45-degree angle to project a floating, semi-transparent image. Thin-film interference interacts with this setup in two distinct ways:

#### 1. The Accidental Problem (Cheap Polymer Foils)

Many modern or DIY Pepper's Ghost setups use stretched polymer plastic films (like Mylar or window insulation film) instead of heavy glass.

- **The Rainbow Artifact:** If the plastic film is ultra-thin and has slight variations in thickness or stretching tension, the ambient room light will cause thin-film interference.
- **The Consequence:** The audience will see distracting, oily rainbow rings (similar to Newton's rings) hovering across the "invisible" screen, ruining the illusion of a clean, empty stage.

#### 2. The Intentional Solution (Dielectric Beamsplitters)

To combat double-reflections (ghostly blurring) and unwanted glare, high-end Pepper's Ghost systems use specialized dielectric beamsplitter glass.

- **Controlled Thin Films:** These glasses are coated with multiple sub-microscopic layers of materials with varying refractive indices.
- **Anti-Reflective Tuning:** Instead of letting random rainbow hues bounce around, engineers precisely calculate the thickness of these coatings to trigger destructive interference for unwanted glare wavelengths. This cancels out reflections from the back of the glass while boosting a sharp, crisp reflection on the front.
