"""LangChain tools for VAP media production."""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from vap import VapClient


# ─────────────────────────────────────────────────────────────────────────
# INPUT SCHEMAS
# ─────────────────────────────────────────────────────────────────────────

class ProductionInput(BaseModel):
    """Input for VapProductionTool."""
    prompt: str = Field(description="Creative prompt describing what to produce")
    preset: str = Field(
        default="streaming_campaign",
        description="Preset to use: streaming_campaign ($5.90), full_production ($7.90)"
    )


class VideoInput(BaseModel):
    """Input for VapVideoTool."""
    prompt: str = Field(description="Description of the video to generate")
    duration: int = Field(default=6, description="Video duration in seconds (4, 6, or 8)")


class MusicInput(BaseModel):
    """Input for VapMusicTool."""
    prompt: str = Field(description="Description of the music to generate (mood, genre, instruments)")
    duration: int = Field(default=120, description="Music duration in seconds (30-480)")


class ImageInput(BaseModel):
    """Input for VapImageTool."""
    prompt: str = Field(description="Description of the image to generate")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4")


# ─────────────────────────────────────────────────────────────────────────
# MAIN TOOL: PRODUCTION (Recommended)
# ─────────────────────────────────────────────────────────────────────────

class VapProductionTool(BaseTool):
    """
    VAP Production Tool - One call, production-ready output.
    
    Use this tool when you need to create video content with music and thumbnails.
    It handles everything in a single call: video, background music, thumbnail, and metadata.
    
    Example prompts:
    - "Energetic startup launch video with upbeat music"
    - "Cozy coffee shop morning scene with gentle acoustic vibes"
    - "Epic product reveal with dramatic orchestral music"
    """
    
    name: str = "vap_production"
    description: str = """Create production-ready video content with music and thumbnails.
Use this for ANY video/media production request. Returns video URL, music URL, thumbnail URL.
Cost: $5.90 (streaming_campaign) or $7.90 (full_production)."""
    
    args_schema: Type[BaseModel] = ProductionInput
    
    api_key: str = Field(description="VAP API key")
    base_url: str = Field(default="https://api.vapagent.com")
    
    def __init__(self, api_key: str, base_url: str = "https://api.vapagent.com", **kwargs):
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
    
    def _run(
        self,
        prompt: str,
        preset: str = "streaming_campaign",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute production preset."""
        client = VapClient(api_key=self.api_key, base_url=self.base_url)
        
        try:
            result = client.execute_preset(preset=preset, prompt=prompt)
            
            outputs = result.outputs
            return f"""Production complete!
- Video: {outputs.get('video', 'N/A')}
- Music: {outputs.get('music', 'N/A')}
- Thumbnail: {outputs.get('thumbnail', 'N/A')}
- Cost: ${result.cost}"""
        
        except Exception as e:
            return f"Production failed: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────
# SINGLE ASSET TOOLS
# ─────────────────────────────────────────────────────────────────────────

class VapVideoTool(BaseTool):
    """
    VAP Video Tool - Generate a single video.
    
    Use this when you ONLY need a video without music or thumbnails.
    For full production with music, use VapProductionTool instead.
    """
    
    name: str = "vap_video"
    description: str = """Generate a single video from a text prompt.
Use this ONLY when you need just a video. For video + music + thumbnail, use vap_production instead.
Cost: $1.90"""
    
    args_schema: Type[BaseModel] = VideoInput
    
    api_key: str = Field(description="VAP API key")
    base_url: str = Field(default="https://api.vapagent.com")
    
    def __init__(self, api_key: str, base_url: str = "https://api.vapagent.com", **kwargs):
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
    
    def _run(
        self,
        prompt: str,
        duration: int = 6,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Generate video."""
        client = VapClient(api_key=self.api_key, base_url=self.base_url)
        
        try:
            result = client.execute_preset(
                preset="video.basic",
                prompt=prompt,
            )
            return f"Video generated: {result.outputs.get('video', 'N/A')} (Cost: ${result.cost})"
        except Exception as e:
            return f"Video generation failed: {str(e)}"


class VapMusicTool(BaseTool):
    """
    VAP Music Tool - Generate background music.
    
    Use this when you need standalone music/audio.
    """
    
    name: str = "vap_music"
    description: str = """Generate music from a text prompt describing mood, genre, instruments.
Cost: $0.59"""
    
    args_schema: Type[BaseModel] = MusicInput
    
    api_key: str = Field(description="VAP API key")
    base_url: str = Field(default="https://api.vapagent.com")
    
    def __init__(self, api_key: str, base_url: str = "https://api.vapagent.com", **kwargs):
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
    
    def _run(
        self,
        prompt: str,
        duration: int = 120,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Generate music."""
        client = VapClient(api_key=self.api_key, base_url=self.base_url)
        
        try:
            result = client.execute_preset(
                preset="music.basic",
                prompt=prompt,
            )
            return f"Music generated: {result.outputs.get('music', 'N/A')} (Cost: ${result.cost})"
        except Exception as e:
            return f"Music generation failed: {str(e)}"


class VapImageTool(BaseTool):
    """
    VAP Image Tool - Generate a single image.
    
    Use this when you need a standalone image/thumbnail.
    """
    
    name: str = "vap_image"
    description: str = """Generate an image from a text prompt.
Cost: $0.29"""
    
    args_schema: Type[BaseModel] = ImageInput
    
    api_key: str = Field(description="VAP API key")
    base_url: str = Field(default="https://api.vapagent.com")
    
    def __init__(self, api_key: str, base_url: str = "https://api.vapagent.com", **kwargs):
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
    
    def _run(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Generate image."""
        client = VapClient(api_key=self.api_key, base_url=self.base_url)
        
        try:
            result = client.execute_preset(
                preset="image.basic",
                prompt=prompt,
            )
            return f"Image generated: {result.outputs.get('image', result.outputs.get('thumbnail', 'N/A'))} (Cost: ${result.cost})"
        except Exception as e:
            return f"Image generation failed: {str(e)}"