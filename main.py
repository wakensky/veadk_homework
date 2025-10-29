import asyncio
import time
from typing import Optional

from google.adk.tools import ToolContext

from veadk import Agent
from veadk import Runner
from veadk.tools.builtin_tools.image_generate import image_generate
from veadk.tools.builtin_tools.video_generate import video_generate


async def image_generation(
    prompt: str,
    *,
    size: str = "2048x2048",
    watermark: bool = False,
    tool_context: ToolContext,
):
  tasks = [
    {
      "task_type": "text_to_single",
      "prompt": prompt,
      "size": size,
      "response_format": "url",
      "watermark": watermark,
    }
  ]
  return await image_generate(tasks=tasks, tool_context=tool_context)


async def video_generation(
    prompt: str,
    *,
    video_name: Optional[str] = None,
    first_frame: Optional[str] = None,
    last_frame: Optional[str] = None,
    resolution: str = "720p",
    ratio: str = "4:3",
    duration_seconds: int = 10,
    watermark: bool = False,
    tool_context: ToolContext,
):
  prompt_with_commands = (
    f"{prompt} --rs {resolution} --rt {ratio} --dur {duration_seconds} --wm {'true' if watermark else 'false'}"
  )
  params = [
    {
      "video_name": video_name or f"video_{int(time.time() * 1000)}",
      "prompt": prompt_with_commands,
    }
  ]

  if first_frame:
    params[0]["first_frame"] = first_frame
  if last_frame:
    params[0]["last_frame"] = last_frame

  return await video_generate(params=params, tool_context=tool_context)


if __name__ == "__main__":
  image_agent = Agent(
    name="image_generation",
    description="Generate single images for use as keyframes.",
    instruction=(
      "Given a user prompt, call the `image_generation` tool to create images. "
      "Prefer 2048x2048 output, URL response format, and disable watermarks."
    ),
    tools=[image_generation],
  )

  video_agent = Agent(
    name="video_generation_with_fixed_first_and_last_frame",
    description="Generate a 10-second, 720p video constrained by first/last frames.",
    instruction=(
      "Use the `video_generation` tool to synthesize a 10-second video at 720p (4:3). "
      "If provided, honor first and last frame image URLs and disable watermarks."
    ),
    tools=[video_generation],
  )

  ensemble_agent = Agent(
    name="ensemble_agent",
    description="Orchestrate image and video agents to produce a guided video.",
    instruction=(
      "First transfer to the `image_generation` agent, call it twice to produce suitable first frame image and last frame image. "
      "Then transfer the output images to the `video_generation_with_fixed_first_and_last_frame` agent, passing those image URLs as inputs, and generate a video."
    ),
    sub_agents=[image_agent, video_agent],
  )

  runner = Runner(
    agent=ensemble_agent,
    app_name="veadk-homework",
    user_id="veadk-homework-user",
  )

  response = asyncio.run(
    runner.run(messages="蜡笔小新在扭腰跳舞", session_id="veadk-homework-sess2")
  )
  print(response)

