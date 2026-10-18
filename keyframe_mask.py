import torch
import re

class KeyframeMask:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "keyframes": ("STRING", {"default": "5:1, 10:0", "multiline": False}),
                "frame_count": ("INT", {"default": 24, "min": 1, "max": 10000}),
                "width": ("INT", {"default": 512, "min": 16, "max": 8192}),
                "height": ("INT", {"default": 512, "min": 16, "max": 8192}),
                "interpolation": (["linear", "hold"],),
            },
            "optional": {
                "size_reference": ("MASK",), # 淨係拎 W/H
                "duration_reference": ("MASK",), # 淨係拎 B = 總張數
            }
        }
    RETURN_TYPES = ("MASK",)
    FUNCTION = "create"
    CATEGORY = "H3-LongTakeNoCuts"

    def create(self, keyframes, frame_count, width, height, interpolation, size_reference=None, duration_reference=None):

        # 1. 如果有插 size ref，就用佢個 W/H
        if size_reference is not None:
            height = size_reference.shape[1]
            width = size_reference.shape[2]

        # 2. 如果有插 duration ref，就用佢個 batch 數
        if duration_reference is not None:
            frame_count = duration_reference.shape[0]

        # parse 5:1, 10:0
        kfs = []
        for part in keyframes.split(","):
            m = re.match(r"\s*(\d+)\s*:\s*([0-9\.]+)\s*", part)
            if m:
                kfs.append((int(m.group(1)), float(m.group(2))))
        kfs = sorted(kfs, key=lambda x: x[0])
        if not kfs:
            kfs = [(0, 1.0)]

        masks = []
        for f in range(frame_count):
            if f <= kfs[0][0]:
                v = kfs[0][1]
            elif f >= kfs[-1][0]:
                v = kfs[-1][1]
            else:
                for i in range(len(kfs)-1):
                    f0, v0 = kfs[i]
                    f1, v1 = kfs[i+1]
                    if f0 <= f <= f1:
                        if interpolation == "hold" or f1==f0:
                            v = v0
                        else:
                            t = (f - f0) / (f1 - f0)
                            v = v0 + (v1 - v0) * t
                        break
            v = max(0.0, min(1.0, v))
            masks.append(torch.full((height, width), v, dtype=torch.float32))

        return (torch.stack(masks),)