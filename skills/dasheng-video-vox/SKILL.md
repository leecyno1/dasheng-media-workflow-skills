---
name: dasheng-video-vox
description: Build question-led VOX-style editorial explainers with one Image2 scene still per micro-shot, crop-storyboard approval, one-shot image-to-video generation, real evidence footage, data, counterarguments, Remotion composition, and governed QC. Use for investigative faceless videos that must be distinct from ordinary article-led explainers.
---

# Dasheng VOX Video

Build an independent `vox_explainer_video` lane. Do not restyle `explainer_html_video` or recite article chapters. For complete production and provider routing, use `dasheng-vox-skills`; this Skill remains its director and visual-grammar component.

Read [references/visual-grammar.md](references/visual-grammar.md) before designing the storyboard.

## Workflow

1. Lock one central question.
2. Build 3-6 evidence pillars from the confirmed Draft and verified data sources.
3. Create one `vox_visual_bible.json` before drawing scenes. Lock the paper/material system, palette, typography, hero objects, spatial world, camera grammar and sound vocabulary.
4. Separate fact, opinion, inference, forecast, rumor, and unknown.
5. Use this narrative order:

   `cold_open -> central_question -> evidence_map -> historical_context -> mechanism_explainer -> field_or_human_evidence -> counterargument -> data_resolution -> qualified_conclusion`

6. Split the narration into director shots averaging 8-12 seconds. Each shot must define one completed reference composition and an ordered assembly choreography for a single 10-second Omni clip.
7. Review the written micro-shot plan before downloading evidence or generating assets.
8. Pass Claim/Evidence before asset production.
9. Search exact entities, events, people, dates, and claims. Prefer direct news, interviews, speeches, archival footage, on-site footage, source documents, and real data over generic B-roll.
10. Run `scripts/video_vox_omni_pack.py` to create one reference-image prompt and one Omni motion prompt for every director shot. Generate the first approved scene still as the master style reference.
11. Generate every complete 16:9 reference still with Codex built-in `imagegen`, save it to the declared project path, and never use Chrome or Gemini for reference-image generation. Keep it flat and separable: one matte background, optional torn base panel, and 4-6 major movable groups with generous gaps. It is the object map Omni must assemble, not a photorealistic scene or the final edited video.
12. Crop every still into 16:9, 1:1 and 9:16 using the declared focus and shot scale. Review the source image and all three crops in `storyboard_contact_sheet.jpg`; reject cut faces, evidence objects, charts or motion paths.
13. Use `dasheng-video-omni-browser` as the default shot generator. Upload the complete reference image and matching prompt to the signed-in Chrome Gemini Omni page; download one approximately 10-second MP4 per shot.
14. Omni must begin on the persistent background/base layer, assemble named paper groups independently, finish by 9 seconds and hold the supplied composition for the final second. Reject full-poster openings followed by deconstruction, uniform push-ins, camera drift, morphing and newly invented objects.
15. Inspect every generated clip. Reject cut edges, baked-in authoritative text, object drift, broken collage geometry, flashes or an unstable final hold.
16. Import approved Omni clips into the dedicated `vox-editorial-collage` Remotion family. Add real evidence, exact text, charts, captions, audio and any local layer animation during this second edit.
17. Pass renderer asset, renderer contract, full render QC, and final delivery identity gates.

## Director rules

- Default to `1920x1080`, `16:9`, `30fps`. Create square or vertical adaptations separately.
- Open with real footage plus animated title, central question/evidence map, data or rule layer, and full captions.
- The default visual world is editorial paper collage: a flat bold paper background, torn base panels, halftone cut-outs, taped source screens, red-thread relationships and physicalized charts. Depth belongs to short paper shadows and later Remotion compositing, not a generated 3D diorama.
- Change the canvas only when narrative responsibility changes. Inside a scene, move through evidence with object transforms and camera choreography.
- Use the motion vocabulary visible in the reference samples: slide, collide, hinge, page-turn, stack, connect, converge and dismantle. Smooth whole-frame drift is not VOX motion.
- During final Remotion editing, put overlays and real footage at distinct Z depths. Do not ask Omni to fake a cinematic 3D world or camera move inside a reference-poster shot.
- Target one 10-second Omni clip per director shot; trim the downloaded clip to the narration beat only during the final edit.
- Use one master reference frame per visual world to constrain palette, materials, typography and object identity. Generate it first and make later Image2 jobs depend on it. Do not let every shot invent a new style.
- Let the script splitter produce paired reference-image and Omni prompts. The narration beat controls the final trim; Omni generation remains 10 seconds.
- Treat crop design as shot design: wide, medium, close and detail shots must produce visibly different framing, not identical full-frame images with different labels.
- Generated text is never authoritative. Headlines, numbers, dates, citations and chart labels must be overlaid exactly in Remotion.
- Treat central news anchors as PIP or split-screen unless the original statement or lower third is direct evidence.
- Keep source charts complete with `contain` before magnification. Do not show a reconstructed chart beside the original chart.
- Include at least one counterargument, failure mode, or boundary condition.
- End with a qualified conclusion that states what is known, inferred, and still unknown.
- Keep new high-salience techniques to a few key shots.
- Keep a visible base layer across cuts. Do not use black curtains, white flashes, or per-caption fade-outs.
- Prefer a clean match cut. If a dissolve is necessary, prelap the incoming shot for only 3-4 frames while the outgoing shot stays opaque; longer dissolves create double-evidence ghosting.
- Reserve blank paper or negative space for Remotion text with a visible inner margin. Reject titles that touch the paper edge, sit outside the generated label, or compete with captions.

## Provider policy

- Use `media-downloader` for real material and provenance.
- Use MiniMax CLI for production narration/music by default.
- Use Codex built-in `imagegen` as the only reference-image provider for the VOX Omni lane. Chrome/Gemini begins only after the approved local PNG exists.
- Use the user's signed-in Chrome Gemini Omni page as the default image-to-video route; no Gemini API key is required.
- Keep MiniMax/MMX and Seedance as shot-level reserves only. They must not silently replace Omni for the whole film.
- Never route production through the removed `vox-director`, AtlasCloud, OpenRouter, Replicate, or another third-party service key.

## Required outputs

- `scene_plan.json`
- `vox_visual_bible.json`
- `tool_routing_plan.json`
- `storyboard_template_review.html`
- `claim_evidence_ledger.json`
- `asset_manifest.json`
- `image2_shot_manifest.json`
- `vox_layer_manifest.json`
- `storyboard_contact_sheet.jpg`
- `edit_decisions.json`
- `video_render_qc.json`
- `final_delivery_manifest.json`

Write runtime media under `~/Desktop/自媒体创作`, never inside this Skill.
