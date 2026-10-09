# H3 LongTakeNoCuts

A workflow and custom nodes that attempt to fix the infamous degradation issue in MiniMax H3.

Built on top of the native motion-context example workflow with minimal changes, keeping the workflow as simple as possible. This is not a Director / Extender AIO node. It provides low-level nodes that you can integrate into your own workflow.

## MiniMax H3 Long-Duration Motion-Context Shot Degradation

Video Examples (with and without refine sampling):

[![image](https://github.com/user-attachments/assets/3f0101e6-c150-44fe-a811-94e455d72d82)](https://youtu.be/vqmztq0dMlw)
[![image](https://github.com/user-attachments/assets/73ccce81-5be2-4944-bbe9-d7328af36a7d)](https://youtu.be/CxXeoMoEWNw)
[![image](https://github.com/user-attachments/assets/2b2db659-8829-47ff-b9cf-b01ec8e45e5d)](https://youtu.be/lILj1U_oo-A)
[![image](https://github.com/user-attachments/assets/bd2b44b8-e968-4d28-8294-18b32213f9a4)](https://youtu.be/N1QIYbfLHQ8)

## Why Motion-Context Degrades

When using motion-context or latent save/load to extend a video without cuts, degradation starts to appear around segments 5-6. (*If you use cuts, there is no degradation issue)

Each segment loads the previous latent as ground truth. Every generation introduces a small amount of drift and detail loss, which accumulates over time. This is the "photocopy effect".

## My Solution to H3 Degradation (So Far)

### Core Idea: add additional Resample (Refine), then Blend Back into Latent.

1. **Refine Resample:**
   - An additional sampling stage with only a few steps.
   - Denoising at 0.5-0.6 restores character details and fixes waxy / burnt look and degradation.

2. **Custom Frame Blend Latent Node:**
   Keyframe blending **by frames** in latent space.
   Since motion-context trims the first 22 frames, we blend the current latent into the refined latent from frame 22-44 (adjustable).

## Workflow:
<img width="2937" height="1064" alt="image" src="https://github.com/user-attachments/assets/e5e1e61e-d986-493b-888e-f0a9e9f7beb5" />
<img width="342" height="147" alt="image" src="https://github.com/user-attachments/assets/16ffd461-2911-4e68-bfc8-f5d099d95aa3" />

## Nodes: 
<img width="256" height="256" alt="image" src="https://github.com/user-attachments/assets/f4121897-00ca-44d0-8fdb-bdd404c4051f" />  

` 0:0, 22:0, 44:1 ` it means 0-22f still current latent, blend to refine latent from 22f to 44f. You can change how fast or slow depends you needs.

## Current Limitations:

**1. Background Shift / Dissolve Artifact**

Because the refine pass uses a high denoise value, it will change things. When blending the new refined latent back into the current generation, if `latent_gen` and `latent_refine` have slightly different backgrounds (even with the same prompt), you will see:
- Background shifts and some fine details on the character may also change.
- Sometimes a visible dissolve / crossfade in the transition area.

**TODO / Open Questions:**
- [ ] I tried using a latent noise-mask to refine only the character and not the background. (Might work better with moving shots)
- [ ] Audio artifacts. We need to check how motion-context handles audio in this case.

This fixes character degradation well, but background dissolve / changes can still be an issue.

## Custom Nodes Used in the Workflow
https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context \
https://github.com/kijai/ComfyUI-KJNodes \
https://github.com/yolain/ComfyUI-Easy-Use (optional)

## Installation
In your `custom_nodes` folder, run:
```bash
git clone https://github.com/xyzDist/H3-LongTakeNoCuts.git
