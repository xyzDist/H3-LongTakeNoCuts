"""MiniMax H3 Video Lock - works for any latent

- No mask: full video lock (black = 0.0)
- With mask: white=change, black=lock
- Auto-detects: IMAGE [B,C,H,W], VIDEO [B,C,T,H,W], H3 AV nested latent
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
import comfy.nested_tensor
from comfy_api.latest import ComfyExtension, io

def prepare_mask_to_latent(mask: torch.Tensor, B, T, H, W, device, dtype):
    """Convert regular pixel MASK [H,W] or [F,H,W] or [B,F,H,W] to latent [B,T,H,W]"""
    if mask is None:
        return None
    if mask.dim() == 2:
        mask = mask.unsqueeze(0).unsqueeze(0) # [1,1,H,W]
    elif mask.dim() == 3:
        mask = mask.unsqueeze(0) # [1,F,H,W]

    b, f, mh, mw = mask.shape

    if mh!= H or mw!= W:
        tmp = mask.reshape(b * f, 1, mh, mw).float().cpu()
        tmp = F.interpolate(tmp, size=(H, W), mode='bilinear', align_corners=False)
        mask = tmp.reshape(b, f, H, W)

    if f!= T:
        if f == 1:
            mask = mask.repeat(1, T, 1, 1)
        else:
            new_masks = []
            for bi in range(b):
                m = mask[bi]
                m = m.permute(1, 2, 0).reshape(H * W, 1, f).float()
                m = F.interpolate(m, size=T, mode='linear', align_corners=False)
                m = m.reshape(H, W, T).permute(2, 0, 1)
                new_masks.append(m)
            mask = torch.stack(new_masks, dim=0)

    if b!= B:
        mask = mask[:B] if b > B else mask.repeat((B + b - 1) // b, 1, 1, 1)[:B]

    return mask.to(device=device, dtype=dtype).clamp(0, 1)

def lock_video(latent: dict, mask: torch.Tensor | None = None, invert: bool = False):
    samples = latent.get("samples")
    is_h3_nested = getattr(samples, "is_nested", False)

    if is_h3_nested:
        # ---- H3 AV nested latent: (video [B,C,T,H,W], audio [B,C,Ta] or [B,C,1,Ta]) ----
        video, audio = tuple(samples.unbind())
        if video.ndim == 4:
            video = video.unsqueeze(0)
        B, C, T, H, W = video.shape

        if mask is not None:
            video_mask = prepare_mask_to_latent(mask, B, T, H, W, video.device, video.dtype)
            if invert:
                video_mask = 1.0 - video_mask
            report_mask_info = f"H3 nested: custom mask mean={video_mask.mean():.3f} shape={tuple(video_mask.shape)}"
        else:
            video_mask = torch.zeros((B, T, H, W), device=video.device, dtype=torch.float32)
            report_mask_info = "H3 nested: full lock (mask=0.0)"

        # audio mask: keep open
        if audio.ndim == 4:
            audio_mask = torch.ones((B, 1, audio.shape[-1]), device=audio.device, dtype=torch.float32)
            audio_len = audio.shape[-1]
        else:
            audio_mask = torch.ones((B, audio.shape[-1]), device=audio.device, dtype=torch.float32)
            audio_len = audio.shape[-1]

        new_masks = comfy.nested_tensor.NestedTensor((video_mask, audio_mask))
        out = dict(latent)
        out["samples"] = comfy.nested_tensor.NestedTensor((video, audio))
        out["noise_mask"] = new_masks

        duration_s = round(int(audio_len) / 40.0, 3)
        report = f"{report_mask_info}, audio open. Audio len {int(audio_len)} (~{duration_s}s). Video {tuple(video.shape)}"

    else:
        # ---- Regular LATENT: [B,C,H,W] or [B,C,T,H,W] ----
        latent_tensor = samples
        if latent_tensor.ndim == 5:
            B, C, T, H, W = latent_tensor.shape
            is_video = True
        elif latent_tensor.ndim == 4:
            B, C, H, W = latent_tensor.shape
            T = 1
            is_video = False
        else:
            raise ValueError(f"Unexpected LATENT shape {tuple(latent_tensor.shape)}")

        if mask is not None:
            video_mask = prepare_mask_to_latent(mask, B, T, H, W, latent_tensor.device, latent_tensor.dtype)
            if invert:
                video_mask = 1.0 - video_mask
            if not is_video:
                # For image latent, Comfy expects [B,H,W]
                if video_mask.ndim == 4:
                    video_mask = video_mask[:, 0] # [B,H,W]
            report_mask_info = f"Regular {'video' if is_video else 'image'} latent: custom mask mean={video_mask.mean():.3f} shape={tuple(video_mask.shape)}"
        else:
            if is_video:
                video_mask = torch.zeros((B, T, H, W), device=latent_tensor.device, dtype=torch.float32)
            else:
                video_mask = torch.zeros((B, H, W), device=latent_tensor.device, dtype=torch.float32)
            report_mask_info = f"Regular {'video' if is_video else 'image'} latent: full lock (mask=0.0)"

        out = dict(latent)
        out["noise_mask"] = video_mask
        report = f"{report_mask_info}, latent {tuple(latent_tensor.shape)}"

    return out, report

class H3VideoLock(io.ComfyNode):
    """Freeze video latent - works for any latent type"""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="H3VideoLock",
            display_name="H3 Video Lock",
            description=(
                "Auto-detect LATENT type. No mask = full lock (0.0). "
                "With MASK: white=change, black=lock. Works for IMAGE [B,C,H,W], VIDEO [B,C,T,H,W] and H3 AV nested latent."
            ),
            category="H3-LongTakeNoCuts",
            inputs=[
                io.Latent.Input("latent", tooltip="Any LATENT: image, video, or H3 AV nested latent"),
                io.Mask.Input("mask", optional=True, tooltip="Regular MASK: white=change, black=lock. If not connected, full lock."),
                io.Boolean.Input("invert_mask", default=False, optional=True, tooltip="Invert the mask"),
            ],
            outputs=[
                io.Latent.Output(display_name="latent"),
                io.String.Output(display_name="report"),
            ],
        )

    @classmethod
    def execute(cls, latent, mask=None, invert_mask=False) -> io.NodeOutput:
        out, report = lock_video(latent, mask, invert_mask)
        return io.NodeOutput(out, report)

class H3VideoLockExtension(ComfyExtension):
    async def get_node_list(self):
        return [H3VideoLock]

async def comfy_entrypoint():
    return H3VideoLockExtension()