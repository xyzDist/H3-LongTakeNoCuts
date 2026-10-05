#### H3 LongTakeNoCuts is custom nodes and workflow attempts to fix the infamous degradation issue
## Minimax-H3 long duration motion-context shot degradation discussion:

Video Examples (without and with refine sample):

<img width="547" height="485" alt="image" src="https://github.com/user-attachments/assets/3f0101e6-c150-44fe-a811-94e455d72d82" />
<img width="1304" height="362" alt="image" src="https://github.com/user-attachments/assets/73ccce81-5be2-4944-bbe9-d7328af36a7d" />


## Why Motion-Context Degrades
Motion-context or latent save/load extend video start to have degradation on segmenets > 5-6 single no cuts shots.
Every segment loads the previous latent as ground truth, every segment generation have some drift and lost, This is the "copying effect"

## My Solution to H3 Copying-Effect Degradation

### Core Idea: Refine Resample + Frame Blend
1.  **Refine Resample:** 
    `latent_refine = resample(latent_gen, denoise=0.5-0.6, ref=character_anchor)`
    - Denoise 0.5-0.6 restores character details, fixes waxy/burnt and degradation
    - refresh to latent

2.  **Custom Frame Blend Latent Node (My Node):**
    keyframe blend **by frames** in latent space:


### Current Limitations
This is not perfect yet:

**1. Background Shift / Dissolve Artifact**
Because we are blending in latent space, the background latent also gets blended. When `latent_gen` and `latent_refine` have slightly different backgrounds (even with same prompt), you see:
- Background texture popping
- Sometimes a visible dissolve / crossfade in transition area

**TODO / Open Questions:**
- [ ] How to blend only character latent and keep background 100% from `gen`? Need better masking in latent space, not pixel space.
- [ ] How to avoid dissolve when background changes? Maybe need background anchor as well.

This solves character degradation well, but background consistency is still the bottleneck. Sharing this approach for feedback.



