import torch
import torch.nn.functional as torchF
import math
import comfy.nested_tensor

class H3BlendLatentsByFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent1": ("LATENT", {"description": "Latent 1"}),
                "latent2": ("LATENT", {"description": "Latent 2"}),
                "keyframes": ("STRING", {"default": "0:0, 22:0, 44:1", "multiline": False}),
                "duration": ("FLOAT", {"default": 8.0, "min": 0.1, "max": 3600.0, "step": 0.1}),
                "fps": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 240.0, "step": 1.0}),
                "interpolation": (["linear", "smooth"], {"default": "linear"}),
                "audio_source": (["latent1", "latent2"], {"default": "latent1"}),
                "blend_audio": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent",)
    FUNCTION = "blend"
    CATEGORY = "H3-LongTakeNoCuts"

    def _unpack(self, latent):
        samples = latent.get("samples")
        if hasattr(samples, "is_nested") and samples.is_nested:
            video, audio = samples.unbind()
        elif isinstance(samples, (list, tuple)):
            video, audio = samples[0], samples[1]
        else:
            raise ValueError(f"Unsupported {type(samples)}")
        if video.ndim == 4:
            video = video.unsqueeze(0)
        if audio.ndim == 3:
            audio = audio.unsqueeze(0)
        return video, audio

    def parse_keyframes(self, k_str, total_frames, pixel_total_frames, interp):
        pairs = []
        for part in k_str.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            try:
                pf, v = part.split(":", 1)
                pairs.append((int(pf.strip()), float(v.strip())))
            except:
                continue
        if not pairs:
            return [0.0] * total_frames
        pairs.sort(key=lambda x: x[0])
        ratio = total_frames / max(1, pixel_total_frames)
        latent_pairs = []
        for p, v in pairs:
            lf = int(round(p * ratio))
            lf = max(0, min(total_frames - 1, lf))
            latent_pairs.append((lf, v))
        dedup = {}
        for f, v in latent_pairs:
            dedup[f] = v
        latent_pairs = sorted(dedup.items())
        if latent_pairs[0][0] > 0:
            latent_pairs.insert(0, (0, latent_pairs[0][1]))
        vals = []
        for i in range(total_frames):
            pf, pv = latent_pairs[0]
            nf, nv = latent_pairs[-1]
            for j in range(len(latent_pairs)):
                if latent_pairs[j][0] <= i:
                    pf, pv = latent_pairs[j]
                if latent_pairs[j][0] >= i:
                    nf, nv = latent_pairs[j]
                    break
            if nf == pf:
                t = 0.0
            else:
                t = (i - pf) / (nf - pf)
            if interp == "smooth":
                t = 0.5 * (1 - math.cos(math.pi * t))
            vals.append(pv + (nv - pv) * t)
        return vals

    def _prepare_mask(self, mask, B, T, H, W, device, dtype):
        if mask is None:
            return None
        # pyright: reportAttributeAccessIssue=false
        if mask.dim() == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)  # [1,1,H,W]
        elif mask.dim() == 3:
            mask = mask.unsqueeze(0)  # [1,F,H,W] - Comfy video mask is [F,H,W]

        b, f, mh, mw = mask.shape

        # 1. Spatial downscale FIRST on CPU to avoid 51GB alloc
        if mh != H or mw != W:
            tmp = mask.reshape(b * f, 1, mh, mw).float().cpu()
            tmp = torchF.interpolate(tmp, size=(H, W), mode='bilinear', align_corners=False)
            mask = tmp.reshape(b, f, H, W)

        # 2. Temporal interpolation after spatial is tiny
        if f != T:
            if f == 1:
                mask = mask.repeat(1, T, 1, 1)
            else:
                new_masks = []
                for bi in range(b):
                    m = mask[bi]  # [F,H,W]
                    m = m.permute(1, 2, 0)  # [H,W,F]
                    m = m.reshape(H * W, 1, f).float()
                    m = torchF.interpolate(m, size=T, mode='linear', align_corners=False)
                    m = m.reshape(H, W, T).permute(2, 0, 1)  # [T,H,W]
                    new_masks.append(m)
                mask = torch.stack(new_masks, dim=0)

        # 3. Batch
        if b == 1 and B > 1:
            mask = mask.repeat(B, 1, 1, 1)
        elif b != B:
            if b > B:
                mask = mask[:B]
            else:
                mask = mask.repeat((B + b - 1) // b, 1, 1, 1)[:B]

        return mask.to(device=device, dtype=dtype).clamp(0, 1)

    def blend(self, latent1, latent2, keyframes, duration, fps, interpolation, audio_source, blend_audio, mask=None):
        video1, audio1 = self._unpack(latent1)
        video2, audio2 = self._unpack(latent2)
        if video1.shape != video2.shape:
            raise ValueError(f"Shape mismatch {video1.shape} vs {video2.shape}")

        B, C, T, H, W = video1.shape
        pixel_total_frames = int(round(duration * fps))
        factors = self.parse_keyframes(keyframes, T, pixel_total_frames, interpolation)

        mask_latent = self._prepare_mask(mask, B, T, H, W, video1.device, video1.dtype)

        video_blended = torch.zeros_like(video1)
        for i, fv in enumerate(factors):
            if mask_latent is not None:
                m = mask_latent[:, i, :, :].unsqueeze(1)  # [B,1,H,W]
                eff = fv * m
                video_blended[:, :, i, :, :] = video1[:, :, i, :, :] * (1 - eff) + video2[:, :, i, :, :] * eff
            else:
                video_blended[:, :, i, :, :] = video1[:, :, i, :, :] * (1 - fv) + video2[:, :, i, :, :] * fv

        if blend_audio:
            aT = audio1.shape[-1]
            ab = torch.zeros_like(audio1)
            for t in range(aT):
                idx = int(round(t / max(1, aT - 1) * (T - 1)))
                fv = factors[idx]
                ab[..., t] = audio1[..., t] * (1 - fv) + audio2[..., t] * fv
        else:
            ab = audio1 if audio_source == "latent1" else audio2

        out = dict(latent2)
        out["samples"] = comfy.nested_tensor.NestedTensor((video_blended, ab))
        out.pop("noise_mask", None)

        print(f" ✅ blend done T={T} mask={tuple(mask_latent.shape) if mask_latent is not None else None}")
        return (out,)
