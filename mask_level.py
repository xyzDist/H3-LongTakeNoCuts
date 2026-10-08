import torch

class MaskLevels:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "black_level": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01, "display": "slider"}),
                "white_level": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01, "display": "slider"}),
                "gamma": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0, "step": 0.05}),
            }
        }
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask",)
    FUNCTION = "apply"
    CATEGORY = "H3-LongTakeNoCuts"

    def apply(self, mask, black_level, white_level, gamma):
        # Output Levels logic: 0 -> black_level, 1 -> white_level
        m = mask.clamp(0, 1)
        if gamma != 1.0:
            m = torch.pow(m.clamp(min=1e-6), 1.0 / gamma)
        
        # lerp black -> white
        m = black_level + (white_level - black_level) * m
        
        return (m.clamp(0, 1),)
