"""公开档案敏感片段遮盖 API。

提交档案原文与候选片段（唯一 ID、正整数权重、按 Unicode 码点计数的
左闭右开起止位置），服务从可重叠的候选中选出互不重叠的最优组合：
依次最大化权重总和、遮盖字符数，再以入选 ID 升序列表的字典序裁决。
返回入选 ID、落选 ID 以及用等长 "█" 遮盖后的正文。
"""

from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from .selector import Interval, apply_mask, select_segments

app = FastAPI(
    title="公开档案敏感片段遮盖 API",
    version="1.0.0",
    description=(
        "从候选片段中选出互不重叠（允许端点相接）的最优组合，"
        "并对正文执行等长 █ 遮盖。位置均按 Unicode 码点计数。"
    ),
)


class Segment(BaseModel):
    """候选片段，区间为左闭右开 [start, end)，按 Unicode 码点计数。"""

    id: str = Field(min_length=1, description="片段唯一 ID")
    weight: int = Field(gt=0, description="正整数权重")
    start: int = Field(ge=0, description="起始位置（含），按码点计数")
    end: int = Field(ge=0, description="结束位置（不含），按码点计数")


class RedactRequest(BaseModel):
    text: str = Field(description="档案原文")
    segments: List[Segment] = Field(default_factory=list, description="候选片段列表")

    @model_validator(mode="after")
    def _check_segments(self) -> "RedactRequest":
        n = len(self.text)
        seen = set()
        for seg in self.segments:
            if seg.id in seen:
                raise ValueError(f"片段 ID 重复: {seg.id!r}")
            seen.add(seg.id)
            if seg.start >= seg.end:
                raise ValueError(
                    f"片段 {seg.id!r} 为空或区间非法: start={seg.start}, end={seg.end}"
                )
            if seg.end > n:
                raise ValueError(
                    f"片段 {seg.id!r} 越界: end={seg.end} 超出正文长度 {n}"
                )
        return self


class RedactResponse(BaseModel):
    selected: List[str] = Field(description="入选片段 ID，升序")
    rejected: List[str] = Field(description="落选片段 ID，升序")
    redacted_text: str = Field(description="入选片段被等长 █ 遮盖后的正文")


@app.post("/redact", response_model=RedactResponse, summary="选择最优片段组合并遮盖正文")
def redact(req: RedactRequest) -> RedactResponse:
    selected = set(
        select_segments(
            Interval(id=s.id, weight=s.weight, start=s.start, end=s.end)
            for s in req.segments
        )
    )
    redacted_text = apply_mask(
        req.text,
        ((s.start, s.end) for s in req.segments if s.id in selected),
    )
    return RedactResponse(
        selected=sorted(selected),
        rejected=sorted(s.id for s in req.segments if s.id not in selected),
        redacted_text=redacted_text,
    )


@app.get("/health", summary="健康检查")
def health() -> dict:
    return {"status": "ok"}
