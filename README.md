#### H3 LongTakeNoCuts is custom nodes and workflow attempts to fix the infamous degradation issue
I am using native motion-context example WF on top add and change as minimum, keep the WF as simple as possible. This is not a Director/Extender AIO node. This is low-level nodes and you can use it with your own workflow setup.
## Minimax-H3 long duration motion-context shot degradation discussion:

Video Examples (with and without refine sample stage):

<img width="547" height="485" alt="image" src="https://github.com/user-attachments/assets/3f0101e6-c150-44fe-a811-94e455d72d82" />
<img width="1304" height="362" alt="image" src="https://github.com/user-attachments/assets/73ccce81-5be2-4944-bbe9-d7328af36a7d" />


## Why Motion-Context Degrades
Motion-context or latent save/load extend video start to have degradation on segmenets around 5-6, on generation video without cuts. (*if you do cuts in shot, there is no degradation issue)
Every segment loads the previous latent as ground truth, every generation have some drift and lost, adding up becomes degradation. This is the "copying effect".

## My Solution to H3 Degradation (so far)

### Core Idea: Refine Resample then Blend it back to Latent.
1.  **Refine Resample:** 
    - simple additional sample stage, with few steps
    - denoise 0.5-0.6 restores character details, fixes waxy/burnt and degradation
    - refresh to latent

2.  **Custom Frame Blend Latent Node:**
    keyframe blend **by frames** in latent space:
    as motion-context is trimming head 22 frames, we blend the current latent to refine latent from 22f-44f (you can change)


### Current Limitations
1. Background Shift / Dissolve Artifact**
Because we do a refine in high denoise value, meaning it will change things, blending new refine back to current generation, When `latent_gen` and `latent_refine` have slightly different backgrounds (even with same prompt), you see:
- Background will be change and Perhaps some fine details on character will be change as well.
- Sometimes a visible dissolve / crossfade in transition area

**TODO / Open Questions:**
- [ ] If we just blend the character with mask, would that better? how worst is the background degradation?
- [ ] How to avoid dissolve when background changes? even not sure if it is possible.

This solves character degradation well, but background consistency is still the bottleneck. Sharing this approach for feedback.



