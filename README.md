#### H3-single-long-shot-no-cuts
## minimax-H3 long duration motion-context shot degradation discussion:

## Problem
Motion-context or latent save/load extend video start to have degradation on segmenets > 5-6 single take, no cuts. The main issues are:
1.  **Motion drift**: character / camera slowly deforms
2.  **Context loss**: model forgets the initial motion trajectory
3.  **Memory explosion**: full attention on all frames is impossible


Testing Examples:

<img width="547" height="485" alt="image" src="https://github.com/user-attachments/assets/3f0101e6-c150-44fe-a811-94e455d72d82" />


