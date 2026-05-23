# 🌈 Rainbow Hues on Semi-Transparent Plastic Sheets (Pepper's Ghost Display)

**Problem:** When viewing the Silver Warrior scene in the physical 6-layer Pepper's Ghost setup (transparent plastic sheets between stacked monitors), rainbow-colored hues appear that are NOT visible when viewing the same layer images on a digital screen. The rainbow artifacts are visible to the naked eye in the plastic but not in the source PNGs.

---

## Answer: Thin-Film Interference

The rainbow hues are caused by **thin-film interference** — the same optical phenomenon behind oil slicks on water and soap bubble iridescence.

### Why The Plastic Sheets Show Rainbows (But Screens Don't)

When looking at a monitor, you're looking at an **emissive light source** — the screen controls exactly which wavelengths hit your eye.

A semi-transparent plastic sheet behaves differently. Light from the monitor behind it passes through the sheet, but:

1. **The Nanometer Trap:** The plastic sheet is incredibly thin — close to the wavelength of visible light (400–700 nm).

2. **The Split Light Wave:** Light hits the sheet. Some reflects off the front surface, some passes through and reflects off the back surface. These two reflections are nearly in sync.

3. **Constructive Interference:** If the sheet thickness matches a specific wavelength, those light waves reinforce each other — producing a vivid, metallic color at that spot.

4. **The Fluid Rainbow:** No plastic sheet is perfectly uniform. Thickness varies by nanometers across the surface, causing the boosted wavelength to shift across the spectrum — creating the rainbow sweep.

### Why This Scene Triggers It More Than Others

The Silver Warrior scene has large areas of uniform color (white snow, blue sky, pale mountains). These expose the rainbow artifact more than scenes with busy, high-contrast detail that visually "mask" the interference pattern.

### Additional Contributors in Our Setup

- **Chroma-key edge fringing:** The green-to-alpha transition has sub-pixel color bleed invisible on screen but amplified when light passes through physical plastic.
- **Polarization:** Monitors emit polarized light. The 6 stacked plastic sheets can act as polarizing filters at certain viewing angles (Monitor #3 already has known polarization issues).
- **Multiple stacked sheets:** 6 layers of plastic compound the interference — each sheet adds its own thin-film effect on top of the previous one.

### How This Applies to Pepper's Ghost Displays

A Pepper's Ghost display uses a clear pane (glass or polymer film) placed at an angle to create a floating, semi-transparent image. Thin-film interference affects this:

#### Accidental Artifact (Cheap Polymer Films)

Stretched polymer plastic films (like Mylar or window insulation) used in DIY Pepper's Ghost rigs:

- **The Rainbow Artifact:** Ultra-thin plastic with thickness/stretching variations causes interference.
- **The Consequence:** Oily rainbow rings (Newton's rings) hover across the "invisible" screen, breaking the illusion of an empty stage.

#### Professional Solution (Dielectric Beamsplitters)

High-end Pepper's Ghost systems use dielectric beamsplitter glass with engineered coatings:

- **Controlled Thin Films:** Coated with sub-microscopic layers of varying refractive indices.
- **Anti-Reflective Tuning:** Thicknesses calculated to create **destructive** interference for glare wavelengths, canceling unwanted reflections while boosting a sharp primary reflection.
