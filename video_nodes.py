from pathlib import Path

try:
    import folder_paths
except ImportError:  # Allows unit tests outside ComfyUI.
    folder_paths = None

from .models import NODE_CATEGORY


class LLMVideoOutput:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"video": ("VIDEO",)}}

    OUTPUT_NODE = True
    FUNCTION = "save"
    CATEGORY = NODE_CATEGORY
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)

    def save(self, video):
        output_dir = folder_paths.get_output_directory()
        folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            "video/LLM_%year%%month%%day%_%hour%%minute%%second%", output_dir
        )
        file = f"{filename}_{counter:05}_.mp4"
        path = Path(folder) / file
        video.save_to(str(path), format="mp4", codec="auto")
        return {
            "ui": {
                "images": [{"filename": file, "subfolder": subfolder, "type": "output"}],
                "animated": (True,),
            },
            "result": (str(path),),
        }
