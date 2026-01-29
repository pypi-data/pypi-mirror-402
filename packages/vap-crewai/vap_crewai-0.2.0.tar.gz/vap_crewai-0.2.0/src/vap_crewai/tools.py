"""CrewAI tools for VAP media production.

This module provides CrewAI-compatible tools for video, music, and image generation
using the VAP (Video/Audio Production) platform.

Directive: #406 (CrewAI Wrapper Implementation)
"""

import os
from typing import Optional

from crewai import Agent
from crewai.tools import tool

from vap import VapClient


# ─────────────────────────────────────────────────────────────────────────
# CLIENT HELPER
# ─────────────────────────────────────────────────────────────────────────

def _get_client(api_key: Optional[str] = None) -> VapClient:
    """
    Get VAP client instance.
    
    Args:
        api_key: Optional API key. If not provided, uses VAP_API_KEY env var.
    
    Returns:
        VapClient instance
    
    Raises:
        ValueError: If no API key is available
    """
    key = api_key or os.getenv("VAP_API_KEY")
    if not key:
        raise ValueError(
            "VAP_API_KEY not set. Either pass api_key parameter or set VAP_API_KEY environment variable."
        )
    return VapClient(api_key=key)


# ─────────────────────────────────────────────────────────────────────────
# MAIN TOOL: PRODUCTION (Recommended)
# ─────────────────────────────────────────────────────────────────────────

@tool("VAP Production")
def vap_production_tool(prompt: str, preset: str = "streaming_campaign") -> str:
    """
    Create production-ready video content with music and thumbnails.
    Use this for ANY video/media production request.
    
    This is the recommended tool for most use cases - it handles everything
    in a single call: video, background music, thumbnail, and metadata.
    
    Args:
        prompt: Creative description of what to produce. Be specific about
                mood, style, and content. Example: "Energetic startup launch
                video with upbeat electronic music"
        preset: Production preset to use:
                - streaming_campaign ($5.90): Video + Music + Thumbnail
                - full_production ($7.90): Higher quality, longer duration
    
    Returns:
        URLs for video, music, and thumbnail with cost breakdown
    
    Example prompts:
        - "Energetic startup launch video with upbeat music"
        - "Cozy coffee shop morning scene with gentle acoustic vibes"
        - "Epic product reveal with dramatic orchestral music"
    """
    client = _get_client()
    
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

@tool("VAP Video")
def vap_video_tool(prompt: str, duration: int = 6) -> str:
    """
    Generate a single video from a text prompt.
    
    Use this ONLY when you need just a video without music or thumbnails.
    For full production with music, use vap_production_tool instead.
    
    Args:
        prompt: Description of the video to generate. Be specific about
                scene, action, mood, and visual style.
        duration: Video duration in seconds (4, 6, or 8). Default: 6
    
    Returns:
        Video URL with cost
    
    Cost: $1.90
    """
    client = _get_client()
    
    try:
        result = client.execute_preset(preset="video.basic", prompt=prompt)
        return f"Video: {result.outputs.get('video', 'N/A')} (Cost: ${result.cost})"
    except Exception as e:
        return f"Video generation failed: {str(e)}"


@tool("VAP Music")
def vap_music_tool(prompt: str, duration: int = 120) -> str:
    """
    Generate music from a text prompt.
    
    Use this when you need standalone background music or audio.
    
    Args:
        prompt: Description of the music to generate. Include mood, genre,
                tempo, and instruments. Example: "Upbeat electronic track
                with synths and punchy drums, 120 BPM"
        duration: Music duration in seconds (30-480). Default: 120
    
    Returns:
        Music URL with cost
    
    Cost: $0.59
    """
    client = _get_client()
    
    try:
        result = client.execute_preset(preset="music.basic", prompt=prompt)
        return f"Music: {result.outputs.get('music', 'N/A')} (Cost: ${result.cost})"
    except Exception as e:
        return f"Music generation failed: {str(e)}"


@tool("VAP Image")
def vap_image_tool(prompt: str, aspect_ratio: str = "16:9") -> str:
    """
    Generate an image from a text prompt.
    
    Use this when you need a standalone image or thumbnail.
    
    Args:
        prompt: Description of the image to generate. Be specific about
                subject, style, lighting, and composition.
        aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4). Default: 16:9
    
    Returns:
        Image URL with cost
    
    Cost: $0.29
    """
    client = _get_client()
    
    try:
        result = client.execute_preset(preset="image.basic", prompt=prompt)
        return f"Image: {result.outputs.get('image', result.outputs.get('thumbnail', 'N/A'))} (Cost: ${result.cost})"
    except Exception as e:
        return f"Image generation failed: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────
# PRE-CONFIGURED AGENT
# ─────────────────────────────────────────────────────────────────────────

def VapProducerAgent(api_key: Optional[str] = None, verbose: bool = True) -> Agent:
    """
    Pre-configured Producer Agent for CrewAI.
    
    Use this agent in your crew for all media production tasks.
    It comes pre-loaded with all VAP tools and an optimized role/backstory.
    
    Args:
        api_key: Optional VAP API key. If not provided, uses VAP_API_KEY env var.
        verbose: Whether to enable verbose output. Default: True
    
    Returns:
        CrewAI Agent configured for video production
    
    Example:
        from crewai import Crew, Task
        from vap_crewai import VapProducerAgent
        
        producer = VapProducerAgent()
        
        task = Task(
            description="Create an energetic startup launch video",
            agent=producer,
        )
        
        crew = Crew(agents=[producer], tasks=[task])
        result = crew.kickoff()
    """
    # Set API key in environment if provided
    if api_key:
        os.environ["VAP_API_KEY"] = api_key
    
    return Agent(
        role="Video Producer",
        goal="Create high-quality video content with music and visuals that perfectly match the creative brief",
        backstory="""You are an expert video producer with access to 
professional production tools. You can create videos, music, 
and images from text descriptions. You have years of experience
in content creation for marketing, social media, and entertainment.
You always deliver production-ready content that exceeds expectations.

Your tools:
- vap_production_tool: Full production (video + music + thumbnail) - Best for most cases
- vap_video_tool: Single video only
- vap_music_tool: Background music
- vap_image_tool: Static images/thumbnails

Always prefer vap_production_tool for complete content packages.""",
        tools=[vap_production_tool, vap_video_tool, vap_music_tool, vap_image_tool],
        verbose=verbose,
    )