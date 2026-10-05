from .h3_blend_latents_by_frames import H3BlendLatentsByFrames

NODE_CLASS_MAPPINGS = {
    "H3BlendLatentsByFrames": H3BlendLatentsByFrames
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "H3BlendLatentsByFrames": "H3 Blend Latents By Frames"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']