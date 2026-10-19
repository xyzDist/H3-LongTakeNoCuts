# H3 LongTakeNoCuts

A workflow and custom nodes that attempt to fix the infamous degradation issue in MiniMax H3.

Built on top of the native motion-context example workflow with minimal changes, keeping the workflow as simple as possible. This is not a Director / Extender AIO node. It provides low-level nodes that you can integrate into your own workflow.

## MiniMax H3 Long-Duration Motion-Context Shot Degradation
No Masking + Refine >> Video Examples (with and without refine sampling):  
[![image](https://github.com/user-attachments/assets/3f0101e6-c150-44fe-a811-94e455d72d82)](https://youtu.be/vqmztq0dMlw)
[![image](https://github.com/user-attachments/assets/73ccce81-5be2-4944-bbe9-d7328af36a7d)](https://youtu.be/CxXeoMoEWNw)
[![image](https://github.com/user-attachments/assets/2b2db659-8829-47ff-b9cf-b01ec8e45e5d)](https://youtu.be/lILj1U_oo-A)
[![image](https://github.com/user-attachments/assets/bd2b44b8-e968-4d28-8294-18b32213f9a4)](https://youtu.be/N1QIYbfLHQ8)

Character Masking + Refine >> Video Examples:  
3 mins duration oner shot  
[![image](https://github.com/user-attachments/assets/8b3b67ad-6ef1-44c4-8b09-ecc4137d0b3d)](https://youtu.be/Ktp9U1JI-LA)  
[![image](https://github.com/user-attachments/assets/4fe60d9d-a16d-4317-a404-da80327d6345)](https://www.youtube.com/watch?v=Zt1ukAOKOfg)  


## Why Motion-Context Degrades

When using motion-context or latent save/load to extend a video without cuts, degradation starts to appear around segments 5-6. (*If you use cuts, there is no degradation issue)

Each segment loads the previous latent as ground truth. Every generation introduces a small amount of drift and detail loss, which accumulates over time. This is the "photocopy effect".

## My Solution to H3 Degradation

<details>
<summary> some of my posts in Reddit </summary>
https://www.reddit.com/r/StableDiffusion/comments/1x6jui1/h3_longtakenocuts_straight_3mins_video_case_study/  
https://www.reddit.com/r/StableDiffusion/comments/1x0nbr5/h3_degradation_my_turn_attempts_to_fixing/  
https://www.reddit.com/r/StableDiffusion/comments/1wo1iqw/h3_oneshotnocuts_new_test/  
https://www.reddit.com/r/StableDiffusion/comments/1wdkdvi/motioncontext_degradation_discussion_summon_sad/  

</details>

### Core Simple Idea: add additional Resample (Refine), then Blend Back into Latent.
1. **Refine Resample:**
   - An additional sampling stage with only a few steps.
   - Denoising at 0.5-0.6 restores character details and fixes waxy / burnt look and degradation.
   - We generate character mask by SAM3, and feed to 

2. **Custom Frame Blend Latent Node:**
   Keyframe blending **by frames** in latent space.
   Since motion-context trims the first 22 frames, we blend the current latent into the refined latent from frame 22-44 (adjustable).



## Workflow:
<img width="2937" height="1064" alt="image" src="https://github.com/user-attachments/assets/e5e1e61e-d986-493b-888e-f0a9e9f7beb5" />
<img width="562" height="256" alt="image" src="https://github.com/user-attachments/assets/b14420f8-d3f0-4243-befb-6a2a8e1bc239" />
<img width="342" height="147" alt="image" src="https://github.com/user-attachments/assets/16ffd461-2911-4e68-bfc8-f5d099d95aa3" />

## Nodes: 
<img width="203" height="160" alt="image" src="https://github.com/user-attachments/assets/c2749be3-f148-41d9-951d-086a08d4302d" />
<img width="211" height="130" alt="image" src="https://github.com/user-attachments/assets/081a14d2-481a-401d-a298-1397136b6eaa" />
<img width="256" height="256" alt="image" src="https://github.com/user-attachments/assets/f4121897-00ca-44d0-8fdb-bdd404c4051f" />  

[ **Keyframe Mask** ] ` 15:1, 22:0, 30:1 ` keep first 2 default, you can change 30f value, this ensure character keep the same at start (after refine) to connect to previous shot.  
[ **Blend Latent By Frames** ] ` 0:0, 22:0, 44:1 ` it means 0-22f still current latent, blend to refine latent from 22f to 44f. You can change how fast or slow depends you needs.

## Current Limitations:
**It's not a real regen or new fresh latent fix**  
This is a workaround with easier implement to setup, It helps to bring down the degradation to minimum, works very well with moving shots.
but for half and static shots, the subject still will drift to higher contrast and saturation.

**TODO / Open Questions:**
- [x] ~~I tried using a latent noise-mask to refine only the character and not the background. (Might work better with moving shots)~~
- [ ] Audio artifacts. We need to check how motion-context handles audio in this case.


## *** Caution!! ***
make sure checking the H3 motion context node is from 'comfyui-h3-motion-context' (see the little green box),
as I know if you install other forked like 'ComfyUI-H3-Motion-Context-MultiRef' will cause using the wrong node and throw error.
Make sure it is from **NikoDemon80**  
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/27d96f76-6b41-422f-9880-98a52c9a73d0" />



## Custom Nodes Used in the Workflow
https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context \
https://github.com/kijai/ComfyUI-KJNodes \
https://github.com/yolain/ComfyUI-Easy-Use (optional)

## Installation
In your `custom_nodes` folder, run:
```bash
git clone https://github.com/xyzDist/H3-LongTakeNoCuts.git
