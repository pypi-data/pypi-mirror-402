from openrouter import LLMModel
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from uuid import uuid4
import re
import budoux
from textlinebreaker import TextLineBreaker
from researchkit.shared.schemas import ResearchAgentResponse
from enum import Enum


# ------------------------------------------------------------------------------
# LLMs
# ------------------------------------------------------------------------------
grok_4_fast = LLMModel("x-ai/grok-4-fast")
grok_4_1_fast = LLMModel(name="x-ai/grok-4.1-fast")
gemini_3_flash = LLMModel(name="google/gemini-3-flash-preview")
gemini_3_pro = LLMModel(name="google/gemini-3-pro-preview")

budoux_parser = budoux.load_default_japanese_parser()


# ------------------------------------------------------------------------------
# Research
# ------------------------------------------------------------------------------

MAX_TOOL_CALL = 15


# ------------------------------------------------------------------------------
# Video generation
# ------------------------------------------------------------------------------
# Video structure schema
class VideoTelopSchema(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    telop: str = Field(default="")
    speech: str = Field(default="")

class VideoSectionSchema(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = Field(default="")
    telops: List[VideoTelopSchema] = Field(default_factory=list)
    slide: str = Field(default="")
    time_stamp: int = Field(default=0)
    
# Video genearation request schema
class VideoGenerationRequestSchema(BaseModel):
    prompt: str = Field(..., description="Target topic or idea that drives the video generation")
    enable_research: bool = Field(default=True, description="Run research to supplement the prompt before scripting")
    report: str = Field(default="", description="Preexisting research report used when research is disabled")
    speaker: Literal["zundamon", "metan", "kasukabe", "amehare"] = Field(
        default="metan",
        description="Voice avatar that will narrate the video"
    )
    bgm: str = Field(default="assets/audio/bgm2.mp3", description="Background music file path or asset identifier")
    bg_video: str = Field(default="assets/video/bg2.mp4", description="Background video file path or asset identifier")
    slide_mode: Literal["mix", "search", "ai"] = Field(default="search", description="Strategy for sourcing slide images")
    output_path: str = Field(default="")
    
class VideoGenerationResponseSchema(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    video_sections: list[VideoSectionSchema]
    research_result: ResearchAgentResponse
    script: str
    generation_time: int

class VideoStructureSchema(BaseModel):
    # Video meta data
    id: str = Field(default_factory=lambda: uuid4().hex)
    request: Optional[VideoGenerationRequestSchema] = Field(default=None)
    
    width: int = Field(default=1920)
    height: int = Field(default=1080)
    fps: int = Field(default=30)
    output_path: str = Field(default="video.mp4")

    # Assets
    bgm: str = Field(default="")
    bg_video: str = Field(default="")
    sections: List[VideoSectionSchema]
    
class VideoJobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class VideoJobSchema(BaseModel):
    id: str = Field(..., description="Job identifier for the video generation task.")
    status: VideoJobStatus = Field(..., description="Current lifecycle status of the job.")
    video_id: str | None = Field(default=None, description="Video identifier when the job completes.")


class VideoJobRequestSchema(BaseModel):
    job_id: str = Field(..., description="Job identifier for the queued request.")
    video_request: VideoGenerationRequestSchema = Field(..., description="Payload for video generation.")


class VideoJobAcceptedSchema(BaseModel):
    job_id: str = Field(..., description="Job identifier for the queued request.")
    status_url: str = Field(..., description="Endpoint that returns the current job status.")

# ------------------------------------------------------------------------------
# General
# ------------------------------------------------------------------------------
class ServiceStatusSchema(BaseModel):
    status: str = Field(..., description="Service status message.")

def read_document_with_line(filepath: str) -> str:
    with open(filepath, "r") as f:
        lines = f.readlines()
        doc_content_with_lines = "".join([f"{i+1:4d} | {line}" for i, line in enumerate(lines)])
        
        return doc_content_with_lines

def read_document_without_lines(filepath: str) -> str:
    with open(filepath, "r") as f:
        return f.read()
    
def char_count(text: str) -> int:
    if not text:
        return 0

    count = 0.0
    for char in text:
        if char.isdigit() or (char.isascii() and char.isalpha()):
            count += 0.5
        else:
            count += 1.0

    return int(count)

def wrap_japanese_text(text: str, max_width: int, max_row: int=4) -> str:
    if not text:
        return ""

    chunks = budoux_parser.parse(text)
    breaker = TextLineBreaker(chunks)
    phrases: list[str] = []

    for line in breaker:
        tokens = re.split(r"(\s+)", line.strip())
        for token in tokens:
            phrases.append(token)

    num_row = min(char_count(text) // max_width + 1, max_row)
    one_line_width = char_count(text) // num_row + 1

    current_char_count = 0
    lines: list[str] = [""]
    
    for phrase in phrases:
        if current_char_count+char_count(phrase) > one_line_width:
            lines.append("")
            current_char_count = 0
            
        lines[-1] += phrase
        current_char_count += char_count(phrase)

    return "\n".join(lines)


if __name__ == "__main__" :
    result = wrap_japanese_text(text="2025年12月17日に科学誌Scienceに掲載された論文では、Blue Marble Space Institute of Scienceの主任研究員ケン・ウィリフォードが筆頭著者として、これらの相互作用が岩石、水、大気のダイナミクスを記録していると述べている。", max_width=40)
    print(result)
