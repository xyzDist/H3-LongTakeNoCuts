from .h3_blend_latents_by_frames import H3BlendLatentsByFrames
from .mask_level import MaskLevels
from .h3_video_lock import H3VideoLock
from .keyframe_mask import KeyframeMask


NODE_CLASS_MAPPINGS = {
    "H3BlendLatentsByFrames": H3BlendLatentsByFrames,
    "MaskLevels": MaskLevels,
    "H3VideoLock": H3VideoLock,
    "KeyframeMask": KeyframeMask,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "H3BlendLatentsByFrames": "H3 Blend Latents By Frames",
    "H3VideoLock": "H3 Video Lock",
    "MaskLevels": "Mask Levels (black/white/gamma)",
    "KeyframeMask": "Keyframe Mask",
}