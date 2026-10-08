from .h3_blend_latents_by_frames import H3BlendLatentsByFrames
from .mask_level import MaskLevels

NODE_CLASS_MAPPINGS = {
    "H3BlendLatentsByFrames": H3BlendLatentsByFrames,
    "MaskLevels": MaskLevels
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "H3BlendLatentsByFrames": "H3 Blend Latents By Frames",
    "MaskLevels": "Mask Levels (black/white/gamma)"
}