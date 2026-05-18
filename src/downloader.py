import os
import time
from typing import Optional, Callable

from huggingface_hub import snapshot_download, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError


MODEL_DIFFUSERS_4BIT = "unsloth/Qwen-Image-2512-unsloth-bnb-4bit"
MODEL_DIFFUSERS_FULL = "Qwen/Qwen-Image-2512"
MODEL_COMFYUI_GGUF = "unsloth/Qwen-Image-2512-GGUF"
MODEL_EDIT_4BIT = "blanchon/Qwen-Image-Edit-2509-bnb-4bit"
GGUF_FILE = "Qwen-Image-2512-Q4_K_S.gguf"


def download_with_retry(
    download_fn,
    max_retries: int = 5,
    retry_delay: int = 10,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> Optional[str]:
    for attempt in range(1, max_retries + 1):
        try:
            if progress_callback:
                progress_callback(f"Downloading... (attempt {attempt}/{max_retries})", 0)
            result = download_fn()
            if progress_callback:
                progress_callback("Download complete!", 100)
            return result
        except (HfHubHTTPError, OSError, RuntimeError) as e:
            if attempt < max_retries:
                msg = f"Download failed (attempt {attempt}/{max_retries}): {e}. Retrying in {retry_delay}s..."
                if progress_callback:
                    progress_callback(msg, 0)
                print(msg)
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                msg = f"Download failed after {max_retries} attempts: {e}"
                if progress_callback:
                    progress_callback(msg, -1)
                print(msg)
                return None
    return None


def download_diffusers_4bit(
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> Optional[str]:
    def _download():
        if progress_callback:
            progress_callback("Downloading Qwen 4-bit model (diffusers)...", 0)
        path = snapshot_download(
            MODEL_DIFFUSERS_4BIT,
            resume_download=True,
            max_workers=4,
        )
        if progress_callback:
            progress_callback(f"Downloaded to: {path}", 100)
        return path

    return download_with_retry(_download, progress_callback=progress_callback)


def download_comfyui_gguf(
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> Optional[str]:
    def _download():
        if progress_callback:
            progress_callback(f"Downloading GGUF model: {GGUF_FILE}...", 0)
        path = hf_hub_download(
            MODEL_COMFYUI_GGUF,
            GGUF_FILE,
            resume_download=True,
        )
        if progress_callback:
            progress_callback(f"Downloaded to: {path}", 100)
        return path

    return download_with_retry(_download, progress_callback=progress_callback)


def download_qwen_image_edit(
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> Optional[str]:
    def _download():
        if progress_callback:
            progress_callback("Downloading Qwen-Image-Edit 4-bit model...", 0)
        path = snapshot_download(
            MODEL_EDIT_4BIT,
            resume_download=True,
            max_workers=4,
        )
        if progress_callback:
            progress_callback(f"Downloaded to: {path}", 100)
        return path

    return download_with_retry(_download, progress_callback=progress_callback)


def check_diffusers_installed() -> bool:
    try:
        from diffusers import DiffusionPipeline
        _ = DiffusionPipeline
        return True
    except ImportError:
        return False


def check_comfyui_installed() -> bool:
    comfy_main = os.path.join(os.path.dirname(__file__), "comfyui", "main.py")
    return os.path.exists(comfy_main)


def check_model_cached(model_id: str) -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache
        import glob

        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
        pattern = os.path.join(cache_dir, f"models--{model_id.replace('/', '--')}*")
        matches = glob.glob(pattern)
        if not matches:
            return False
        folder = matches[0]
        return os.path.isdir(folder) and len(os.listdir(folder)) > 0
    except Exception:
        return False


if __name__ == "__main__":
    print("Checking installed models...")
    print(f"  Diffusers 4-bit cached: {check_model_cached(MODEL_DIFFUSERS_4BIT)}")
    print(f"  ComfyUI installed: {check_comfyui_installed()}")
