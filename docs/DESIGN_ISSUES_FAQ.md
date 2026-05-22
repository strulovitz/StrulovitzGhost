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
| 3 | **N < 6 handling is weak** | Only 3 good layers → put at L1-L2-L3 (closest, filled first), L4-L5-L6 empty transparent. | ✅ RESOLVED — No problem. L1=closest (20cm) filled FIRST. L6=farthest filled LAST. If only 3 good layers: L1-L2-L3 full content, L4-L5-L6 empty transparent. Viewer never sees through empty far layers because close full layers obstruct them. Fixed numbering in design docs too (was reversed). |
| 4 | **No prompt inheritance** | TTG: worker gets text prompt from Boss. ITG: worker gets IMAGE from parent — but what PROMPT for Qwen-Image-Layered? | ✅ RESOLVED — Each entity has 3 AI capabilities: ✂️ Qwen-Image-Layered (splitter), 👁️ Qwen3-VL (eyes/describes), 🧠 Qwen LLM (brain/writes custom prompt). Flow: split → Qwen3-VL describes each good layer ("hookah glass with smoke") → Qwen LLM writes tailored prompt for child ("Decompose into: glass base, metal stem, smoke wisps") → prompt attached to child task in DB. Child receives BOTH image + customized prompt. |
| 5 | **Z-order is fragile** | Whole pipeline depends on correct depth ordering. Qwen3-VL pairwise could be wrong. Programmatic fallback (coverage-based) is a GUESS — tiny character vs giant cloud would fail. | ✅ RESOLVED — NO programmatic fallback (Nir says it's impossible — giant cloud vs tiny character proves it). Trust Qwen3-VL entirely. If wrong, output is wrong — cost of automation. Can't override Qwen, only human can. Also propagate Client's original prompt through system: if Client describes depth ("foreground X, middle Y, background Z"), feed that context to Qwen3-VL to help it. Removed all programmatic fallback code from design. |

---

## Issues Found by Desktop AI (Review of ITG Design)

| # | Issue | Desktop's Concern | Status |
|---|-------|-------------------|--------|
| 6 | **Z-order flow was unclear → discovered ITG must be POOL, not rigid tree** | Desktop asked "What images does Top Boss download from teachers?" → Led to Nir's clarification: ITG is a TASK POOL. Any free teacher claims any task. Ancestry via filename. Original teacher (who claimed parent) collects children's results. Manager only handles his direct children's final results (max ~36, not hundreds). File naming prevents double-processing. See ITG design §2.1-2.4. | ✅ FIXED — Rewrote entire ITG architecture to POOL model |
| 7 | **Multi-image Qwen3-VL won't work in Ollama** | Original code sent ALL images at once. Ollama supports 1-2 images per call, not N. | ✅ FIXED — switched to pairwise |
| 8 | **File naming mismatched** | Nir wants `task_42_01_02.png` but ancestry was tracked in DB fields. | ✅ FIXED — filename-based ancestry |
| 9 | **Both layers garbage = branch silently dies** | Only handled "1 good + 1 bad." If both bad, parent task stays "claimed" forever. | ✅ FIXED — 3-retry fallback |
| 10 | **ComfyUI port conflict** | Boss + Worker same machine both try port 8188. | ✅ FIXED — port management + serialization |
| 11 | **Extreme aspect ratios** | `thumbnail((640,640))` on panorama → 640×50px. | ✅ FIXED — 640×640 square padding |

---

## Open Questions — TTG Design

| # | Question | Status |
|---|----------|--------|
| 12 | **Should the website auto-cleanup?** Or Client/Boss explicitly call `/cleanup`? | ✅ RESOLVED — Option A: Website auto-cleans temp files when it detects all tasks in a question are complete. No manual trigger needed. |
| 13 | **Can one Boss handle multiple questions simultaneously?** Or locked to one job at a time? | ✅ RESOLVED — Option A: One question at a time. If someone wants another picture, they wait in line or get redirected to another school. |
| 14 | **Worker failure recovery after N retries?** Task resets to pending. What if it fails 5 times in a row? | ✅ RESOLVED — After 3 failures (claimed → reset → claimed → reset → claimed → reset), mark task as `failed`. Not the Workers, it's the task — image is probably corrupted or unsplittable. |
| 15 | **Which Qwen model for hierarchical TTG splitting?** Is `qwen3:14b` good enough for all levels? | ✅ RESOLVED — Upper levels have MORE responsibility (manager's bad split ruins everything downstream). RECOMMENDATION (not demand): upper levels use better hardware + better models (DeepSeek for logic). But software supports ANY model at ANY level — user chooses. Lower levels work with smaller pieces anyway, less thinking needed. |
| 16 | **TTG hierarchical depth — who sets it?** Client? Boss? Each teacher? | ✅ RESOLVED — Hardware determines depth, not software. A school with 500 computers goes deeper than one with 5. Each boss knows how many children they have, divides work accordingly. No boss knows total depth — it's emergent. "Too much detail" won't happen in reality — excess computers just do MORE scenes, not deeper on one scene. |

---

## Open Questions — ITG Design

| # | Question | Status |
|---|----------|--------|
| 17 | **Qwen3-VL model size?** 4B vs 8B vs 30B — which for quality judging? | ✅ RESOLVED — No minimum. Document the options: 4B (fast, modest quality), 8B (balanced), 30B (best, needs strong GPU). User chooses based on their hardware/budget. Software works with ANY size. Smaller = faster but less accurate — still works. |
| 18 | **Is Qwen3-VL available in Ollama?** Never actually tested Ollama's vision API with local Qwen3-VL. | ✅ CONFIRMED — All sizes available: 2B, 4B, 8B, 30B, 32B, 235B. Command: `ollama run qwen3-vl:4b "Describe: /path/to/image.png"`. Works for both quality judging and parent-anchored spatial positioning. ITG design is on solid ground. |
| 19 | **Prompt for Qwen-Image-Layered — STILL UNSOLVED.** Might build whole ITG system, discover model produces garbage 90% of the time for fine art. | ✅ NOT A BLOCKER (see Issue #1). Worked excellent on food+drink table, Eagle Nebula, Opium Dream (4 layers). We build now, investigate prompt syntax later. Feature has value without perfect fine art support. |
| 20 | **SageAttention + Triton for diffusers?** Might allow Python-native splitting without ComfyUI. | ✅ DEFERRED — Yesterday was "a day from hell" with diffusers. ComfyUI works, we stick with it. SageAttention is "maybe someday" research, not a build priority. |
| 21 | **How many workers per Boss?** Exactly 2 (split 1→2)? Or can a Teacher create more? | ✅ RESOLVED by Issue #6 (POOL architecture). We don't control how many good layers Qwen splitter produces. Manager posts however many come out → whoever is free claims them. No fixed count. |
| 22 | **Claim timeout for ITG?** How long before claimed task resets? ITG: ~2-3 min (RTX 5090), ~8-12 min (RTX 4070 Ti). | ✅ RESOLVED — Boss decides timeout, not website (website is just a blackboard). Timeout based on SLOWEST known worker so weak computers don't get tasks stolen mid-work. Default: 15 min (12 min for slowest + 3 min grace). |
| 23 | **N = 1 good layer total?** After all splitting, only 1 layer remains. Success or failure? | ✅ RESOLVED — 1 layer = FAILURE (it's just the original — nothing was split). 2-3 = borderline, subjective. 4+ = minimum for success. Mark question status accordingly so Client knows. |
| 24 | **Should ITG and TTG share the SAME website instance?** Separate servers? Different DBs? | ✅ RESOLVED — SAME database with `type` field. To users, it's ONE system: Strulovitz Ghost. Photo or text input = implementation detail. Same queue, same line. Sharing DB doesn't hurt performance — it makes tracking easier (who's next in line regardless of mode). |

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
