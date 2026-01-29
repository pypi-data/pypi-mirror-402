"""VAP CrewAI Tools - Give your Crew a Studio.

CrewAI tools for VAP (Video/Audio Production). Add a Producer Agent to your crew.

Example:
    from crewai import Crew, Task
    from vap_crewai import VapProducerAgent, vap_production_tool
    
    # Option 1: Use pre-configured Producer Agent
    producer = VapProducerAgent()
    
    # Option 2: Use tools directly with custom agent
    from crewai import Agent
    custom_agent = Agent(
        role="Marketing Lead",
        tools=[vap_production_tool],
        ...
    )
"""

from vap_crewai.tools import (
    vap_production_tool,
    vap_video_tool,
    vap_music_tool,
    vap_image_tool,
    VapProducerAgent,
)

__version__ = "0.1.0"
__all__ = [
    "vap_production_tool",
    "vap_video_tool",
    "vap_music_tool",
    "vap_image_tool",
    "VapProducerAgent",
]