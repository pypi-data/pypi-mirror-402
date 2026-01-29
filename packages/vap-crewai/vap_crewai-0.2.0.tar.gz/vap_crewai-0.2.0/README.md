# VAP CrewAI Tools

**Execution control for CrewAI crews calling paid APIs.**

CrewAI tools for VAP - the execution control layer. Enforce cost limits and deterministic retries when your crews generate video, music, and images.

[![PyPI version](https://badge.fury.io/py/vap-crewai.svg)](https://pypi.org/project/vap-crewai/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install vap-crewai
```

## Quick Start

```python
import os
from crewai import Crew, Task
from vap_crewai import VapProducerAgent, vap_production_tool

os.environ["VAP_API_KEY"] = "vap_your_api_key"

# Option 1: Use pre-configured Producer Agent
producer = VapProducerAgent()

task = Task(
    description="Create an energetic startup launch video with upbeat music",
    agent=producer,
    expected_output="Video URL, Music URL, and Thumbnail URL"
)

crew = Crew(agents=[producer], tasks=[task])
result = crew.kickoff()
```

### Option 2: Use Tools with Custom Agent

```python
from crewai import Agent
from vap_crewai import vap_production_tool, vap_video_tool

marketing_lead = Agent(
    role="Marketing Lead",
    goal="Create compelling marketing content",
    backstory="Expert in digital marketing with a focus on video content",
    tools=[vap_production_tool, vap_video_tool],
)
```

## Available Tools

| Tool | Description | Cost |
|------|-------------|------|
| `vap_production_tool` | Full production (video + music + thumbnail) | $5.90 |
| `vap_video_tool` | Single video generation | $1.96 |
| `vap_music_tool` | Background music generation | $0.68 |
| `vap_image_tool` | Single image generation | $0.18 |

### Recommended: `vap_production_tool`

For most use cases, use `vap_production_tool` - it handles everything in one call:
- 🎬 Video generation
- 🎵 Background music
- 🖼️ Thumbnail
- 📝 Metadata

## Pre-configured Agent

`VapProducerAgent()` returns a ready-to-use CrewAI Agent with all VAP tools and an optimized configuration:

```python
from vap_crewai import VapProducerAgent

# Basic usage
producer = VapProducerAgent()

# With custom API key
producer = VapProducerAgent(api_key="vap_xxx")

# Disable verbose output
producer = VapProducerAgent(verbose=False)
```

## Multi-Agent Crew Example

```python
from crewai import Crew, Task, Agent
from vap_crewai import VapProducerAgent, vap_production_tool

# Create agents
researcher = Agent(
    role="Content Researcher",
    goal="Research trending topics and content ideas",
    backstory="Expert in market research and trend analysis",
)

producer = VapProducerAgent()

writer = Agent(
    role="Script Writer",
    goal="Write compelling video scripts",
    backstory="Professional copywriter for video content",
)

# Define tasks
research_task = Task(
    description="Research the latest trends in AI technology",
    agent=researcher,
    expected_output="List of trending AI topics with descriptions"
)

script_task = Task(
    description="Write a 30-second video script about the top AI trend",
    agent=writer,
    expected_output="Video script with scene descriptions"
)

production_task = Task(
    description="Create a video based on the script",
    agent=producer,
    expected_output="Video URL, Music URL, Thumbnail URL"
)

# Create and run crew
crew = Crew(
    agents=[researcher, writer, producer],
    tasks=[research_task, script_task, production_task],
    verbose=True
)

result = crew.kickoff()
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VAP_API_KEY` | Your VAP API key (required) |

Get your API key at [vapagent.com](https://vapagent.com)

## Links

- [VAP Documentation](https://docs.vapagent.com)
- [VAP SDK](https://pypi.org/project/vap-sdk/)
- [CrewAI Documentation](https://docs.crewai.com)

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Directive:** #406 (CrewAI Wrapper Implementation)