import torch
import math
import comfy.nested_tensor


class H3BlendLatentsByFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent1": ("LATENT", {
                    "description": "Latent 1（0 = 純 latent1）"
                }),
                "latent2": ("LATENT", {
                    "description": "Latent 2（1 = 純 latent2）"
                }),
                "keyframes": ("STRING", {
                    "default": "0:0, 22:0, 44:1",
                    "multiline": False,
                    "placeholder": "例如: 0:0, 22:0, 44:1（幀號:比例 0=latent1, 1=latent2）"
                }),
                "duration": ("FLOAT", {
                    "default": 8.0,
                    "min": 0.1,
                    "max": 3600.0,
                    "step": 0.1,
                }),
                "fps": ("FLOAT", {
                    "default": 24.0,
                    "min": 1.0,
                    "max": 240.0,
                    "step": 1.0,
                }),
                "interpolation": (["linear", "smooth"], {
                    "default": "smooth"
                }),
                "audio_source": (["latent1", "latent2"], {
                    "default": "latent1",
                    "tooltip": "當 blend_audio 關閉時，選擇使用邊個 latent 嘅 audio（refine 階段建議揀 latent1 避免音質受損）"
                }),
                "blend_audio": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enable",
                    "label_off": "disable",
                }),
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
            raise ValueError(f"[H3Blend] 唔支援嘅 samples 類型: {type(samples)}")
        if video.ndim == 4:
            video = video.unsqueeze(0)
        if audio.ndim == 3:
            audio = audio.unsqueeze(0)
        return video, audio

    def parse_keyframes(self, keyframes_str, total_frames, pixel_total_frames, interpolation):
        pairs = []
        for part in keyframes_str.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            frame_str, value_str = part.split(":", 1)
            try:
                pixel_frame = int(frame_str.strip())
                value = float(value_str.strip())
            except ValueError:
                continue
            pairs.append((pixel_frame, value))

        if not pairs:
            print("[H3Blend] ⚠️ 冇有效 keyframe，全部幀設為 0（純 latent1）")
            return [0.0] * total_frames

        pairs.sort(key=lambda x: x[0])

        ratio = total_frames / max(1, pixel_total_frames)
        latent_pairs = []
        for pixel_frame, value in pairs:
            latent_frame = int(round(pixel_frame * ratio))
            latent_frame = max(0, min(latent_frame, total_frames - 1))
            latent_pairs.append((latent_frame, value))

        dedup = {}
        for f, v in latent_pairs:
            dedup[f] = v
        latent_pairs = sorted(dedup.items())

        if latent_pairs[0][0] > 0:
            latent_pairs.insert(0, (0, latent_pairs[0][1]))

        values = []
        for i in range(total_frames):
            prev_frame, prev_val = latent_pairs[0]
            next_frame, next_val = latent_pairs[-1]
            for j in range(len(latent_pairs)):
                if latent_pairs[j][0] <= i:
                    prev_frame, prev_val = latent_pairs[j]
                if latent_pairs[j][0] >= i:
                    next_frame, next_val = latent_pairs[j]
                    break

            if next_frame == prev_frame:
                t = 0.0
            else:
                t = (i - prev_frame) / (next_frame - prev_frame)

            if interpolation == "linear":
                factor = t
            elif interpolation == "smooth":
                factor = 0.5 * (1 - math.cos(math.pi * t))
            else:
                factor = t

            values.append(prev_val + (next_val - prev_val) * factor)

        return values

    def blend(self, latent1, latent2, keyframes, duration, fps, interpolation, audio_source, blend_audio):
        video1, audio1 = self._unpack(latent1)
        video2, audio2 = self._unpack(latent2)

        if video1.shape != video2.shape:
            raise ValueError(
                f"[H3Blend] 兩個 latent 形狀唔同: "
                f"{tuple(video1.shape)} vs {tuple(video2.shape)}"
            )

        B, C, F, H, W = video1.shape
        pixel_total_frames = int(round(duration * fps))

        factors = self.parse_keyframes(keyframes, F, pixel_total_frames, interpolation)

        video_blended = torch.zeros_like(video1)
        for i, f in enumerate(factors):
            video_blended[:, :, i, :, :] = video1[:, :, i, :, :] * (1 - f) + video2[:, :, i, :, :] * f

        if blend_audio:
            audio_T = audio1.shape[-1]
            audio_blended = torch.zeros_like(audio1)
            for t in range(audio_T):
                video_idx = int(round(t / max(1, audio_T - 1) * (F - 1)))
                f = factors[video_idx]
                audio_blended[..., t] = audio1[..., t] * (1 - f) + audio2[..., t] * f
            audio_mode_str = "已混合 (mixed)"
        else:
            if audio_source == "latent1":
                audio_blended = audio1
                audio_mode_str = "直接使用 latent1"
            else:
                audio_blended = audio2
                audio_mode_str = "直接使用 latent2"

        output = dict(latent2)
        output["samples"] = comfy.nested_tensor.NestedTensor((video_blended, audio_blended))
        output.pop("noise_mask", None)

        print(f"[H3Blend] 🎬 {duration}s × {fps} = {pixel_total_frames} 幀")
        print(f"[H3Blend] 🎯 Keyframes: {keyframes}")
        print(f"[H3Blend] 🔊 Audio: {audio_mode_str}")
        print(f"[H3Blend] ✅ 完成")

        return (output,)