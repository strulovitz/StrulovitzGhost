# 🔍 Design Issues & FAQ — TTG + ITG

**Date:** May 22, 2026 | **Status:** In discussion — going through one at a time with Nir

> This document captures every issue, concern, and open question from both AIs
> (Laptop + Desktop) about the TTG and ITG designs. We go through them ONE BY ONE
> with Nir and update answers here as we resolve them.

---

## Issues Found by Laptop AI While Designing

| # | Issue | Concern | Status |
|---|-------|---------|--------|
| 1 | **Qwen-Image-Layered prompts don't work reliably** | Tested 6+ hours May 21. Empty prompt `""` worked accidentally but no prompt consistently produces non-garbage layers for fine art. Model trained on Photoshop PSDs, not impressionist brushwork. Whole ITG depends on this working. | ⚠️ OPEN — will investigate after build. Market is broader than just "fine art": Hubble photos, Christmas tables, CCTV frames, drone photos, garden planters all worked. Possibly our prompt SYNTAX was wrong (Nir realized today: newline+comma = double-encoding, telling model "one good line + one empty line"). Need to re-test with correct syntax. Feature works even if classic paintings don't — too many other use cases. |
| 2 | **Combining is destructive** | Pair-combine is permanent fusion. If Z-order was wrong, or those 2 layers should have stayed separate (meaningful parallax), there's no undo. Top Boss makes an irreversible call. | ✅ RESOLVED — Combining is DESIRED, not a problem. Client trusts the system, system trusts Qwen3-VL (best local vision models: Qwen3-VL 30B/35B, Gemma 3 4B). Good summaries always omit raw material. If mistake → re-run. For 90% of users, this is sufficient. Professionals who need perfection use Photoshop. |
| 3 | **N < 6 handling is weak** | Only 3 good layers → put at L4-L5-L6, L1-L2-L3 empty transparent. But physical setup expects ALL 6 layers to have content. Empty layers are dead air. Acceptable for Pepper's Ghost? | ⬜ UNRESOLVED |
| 4 | **No prompt inheritance** | TTG: worker gets text prompt from Boss. ITG: worker gets IMAGE from parent — but what PROMPT for Qwen-Image-Layered? Qwen3-VL generates it? Boss writes it manually? | ⬜ UNRESOLVED |
| 5 | **Z-order is fragile** | Whole pipeline depends on correct depth ordering. Qwen3-VL pairwise could be wrong. Programmatic fallback (coverage-based) is a GUESS — tiny foreground character vs giant background cloud could swap. | ⬜ UNRESOLVED |

---

## Issues Found by Desktop AI (Review of ITG Design)

| # | Issue | Desktop's Concern | Status |
|---|-------|-------------------|--------|
| 6 | **Z-order flow was unclear** | "What images does Top Boss download from teachers?" — data flow not specified step by step. | ✅ FIXED |
| 7 | **Multi-image Qwen3-VL won't work in Ollama** | Original code sent ALL images at once. Ollama supports 1-2 images per call, not N. | ✅ FIXED — switched to pairwise |
| 8 | **File naming mismatched** | Nir wants `task_42_01_02.png` but ancestry was tracked in DB fields. | ✅ FIXED — filename-based ancestry |
| 9 | **Both layers garbage = branch silently dies** | Only handled "1 good + 1 bad." If both bad, parent task stays "claimed" forever. | ✅ FIXED — 3-retry fallback |
| 10 | **ComfyUI port conflict** | Boss + Worker same machine both try port 8188. | ✅ FIXED — port management + serialization |
| 11 | **Extreme aspect ratios** | `thumbnail((640,640))` on panorama → 640×50px. | ✅ FIXED — 640×640 square padding |

---

## Open Questions — TTG Design

| # | Question | Status |
|---|----------|--------|
| 12 | **Should the website auto-cleanup?** Or should Client/Boss explicitly call `/cleanup`? | ⬜ UNRESOLVED |
| 13 | **Can one Boss handle multiple questions simultaneously?** Or locked to one job at a time? | ⬜ UNRESOLVED |
| 14 | **Worker failure recovery after N retries?** Currently task resets to pending. What if it fails 5 times in a row? | ⬜ UNRESOLVED |
| 15 | **Which Qwen model for hierarchical splitting?** Currently `qwen3:14b`. Good enough for splitting "a bouquet of flowers" into 6 individual flower descriptions? | ⬜ UNRESOLVED |
| 16 | **TTG hierarchical depth — who sets it?** Client? Boss? Each teacher decides for their own classroom? | ⬜ UNRESOLVED |

---

## Open Questions — ITG Design

| # | Question | Status |
|---|----------|--------|
| 17 | **Qwen3-VL model size?** 4B (fast, might miss nuance) vs 8B (better, heavier). Which for quality judging? | ⬜ UNRESOLVED |
| 18 | **Is Qwen3-VL available in Ollama?** Need to VERIFY — never actually tested Ollama's vision API with local Qwen3-VL. | ⬜ UNRESOLVED |
| 19 | **Prompt for Qwen-Image-Layered — STILL UNSOLVED.** Biggest risk. Might build whole ITG system, discover model produces garbage 90% of the time for fine art. | ⬜ UNRESOLVED |
| 20 | **SageAttention + Triton for diffusers?** Might allow Python-native splitting (no ComfyUI). Worth investigating? | ⬜ UNRESOLVED |
| 21 | **How many workers per Boss?** Exactly 2 (since split is 1→2)? Or should a Teacher run multiple splits and create more children? | ⬜ UNRESOLVED |
| 22 | **Claim timeout for ITG?** How long before claimed-but-not-completed task resets? ITG split: ~2-3 min (RTX 5090), ~8-12 min (RTX 4070 Ti). | ⬜ UNRESOLVED |
| 23 | **What if a painting decomposes into ONLY 1 good layer total?** N=1 after all splitting and judging. Is that a "successful decomposition" or a failure? | ⬜ UNRESOLVED |
| 24 | **Should ITG and TTG share the SAME website instance?** Or separate Flask servers? Same DB? Different DBs? | ⬜ UNRESOLVED |

---

## THE BIGGEST RISK

**We have never seen Qwen-Image-Layered produce a GOOD decomposition of a fine art painting.**

- Starry Night: 7 RGBA files but actual decomposition layers were duplicates/original/blacks
- Only the composite layer (the +1) was "good" — and that's just the original image reconstructed
- The real splitting DID NOT WORK
- 6+ hours, 5 approaches, 4 AI models consulted
- Google AI contradicted itself 4 times
- Model trained on Photoshop PSDs (photos with clear subjects), not Van Gogh's brushstrokes

**UPDATE (May 22, after discussing with Nir):** "Fine Art" is just the marketing name. The feature works on many image types — Eagle Nebula (Hubble), Opium Dream (Boris Vallejo, 4 good layers), Christmas dinner table, etc. It may turn out OUR prompt SYNTAX was wrong (newline+comma = double separator characters). The feature has value even if classic paintings don't work. We build now, investigate prompt syntax later. Not a blocker.

---

## Discussion Log

*(We fill this in as we go through each issue with Nir.)*

| Issue # | Nir's Input | Resolution |
|---------|-------------|------------|
| 1 | "Fine Art" is marketing name. Feature works on Eagle Nebula, Opium Dream (4 layers), Christmas table, etc. Paintings may fail but many other use cases. Prompt syntax possibly our fault (newline+comma = double separator). Build now, investigate later. | ⚠️ OPEN for investigation, but NOT a build blocker. Feature has broad value beyond paintings. |
| 2 | Combining is desired. Client trusts system, system trusts Qwen3-VL. Good summary always omits data. If mistake → re-run. 90% sufficient. Pros use Photoshop. | ✅ RESOLVED |

---

*This document will be updated in real-time as we discuss each issue with Nir.*
