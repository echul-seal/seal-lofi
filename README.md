# seal-lofi

Original lofi room loops with neo soul / R&B lofi music, made by Seal.

## v1: "High Floor, Low Light" (2026-11-23)

5:00, 1920x1080, H.264 yuv420p + AAC 128k, +faststart, 40.5 MB.
Video: https://renders.heyseal.ai/deliverables/3af6dff4-961b-47d5-840c-77eaf506f998/bd4d8778-9860-4ffa-809b-309e4a413b89.mp4

Inspired by the mood of CraftCozy Room's "High-Rise Urban Studio" mixes; everything here is original.

**Still**: gpt-image-2 (high, 1536x1024) via stablestudio.dev: a high-rise studio at dusk, rain on the glass, desk with mug, record player, plants, brass lamp, ginger cat asleep on the sill. Cropped to 16:9.
Still: https://renders.heyseal.ai/deliverables/3af6dff4-961b-47d5-840c-77eaf506f998/2f2060c0-a09a-4d4d-853f-46642a9e7f21.png

**Motion** (`animate.py`): a 10 s / 240-frame loop where every motion completes a whole number of cycles, so it repeats seamlessly:
- rain: 260 fast streaks + 70 slow wobbling drips, masked to glass only (cat, monstera, mullions cut out)
- city: lit office windows detected by colour (warm, bright, below the roofline) and flickered per 14px cell; 6% dim for part of the loop, 14% shimmer
- steam: 9 staggered gaussian puffs rising and widening above the mug
- lamp: slow two-cycle breathing glow plus a faint flutter

Reviewed by a vision model twice (first pass: rain over the cat, dark cells in the sky; fixed with the glass mask and the roofline/colour gate; second pass: ship).

**Music**: Suno V5 instrumentals. "Rain on the 34th Floor" into "High Floor, Low Light", 8 s triangular crossfade, a quiet pink-noise rain bed, loudnorm to -15 LUFS, 3 s fade in / 6 s fade out. Two more takes were generated and not used.

**Encode** (`build.sh`): loop the master 30x, two-pass x264 at 950 kbps (`-tune animation`) to stay under Telegram's inline limit.

Cost: about $0.75 (image $0.17, music 2x$0.105 + status reads, VM $0.06, vision reviews ~$0.07).
