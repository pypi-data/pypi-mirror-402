from __future__ import annotations

import os

from httpx import AsyncClient, Client

from share.util import (
    ServiceStatusSchema,
    VideoGenerationRequestSchema,
    VideoGenerationResponseSchema,
    VideoJobAcceptedSchema,
    VideoJobSchema,
)


class InstantVideoAsyncClient:
    def __init__(self, base_url: str, timeout: float = 1800.0, api_key: str | None = None) -> None:
        normalized_base_url = base_url.rstrip("/")
        resolved_api_key = api_key or os.environ.get("INSTANTVIDEO_API_KEY")

        if not resolved_api_key:
            raise ValueError("INSTANTVIDEO_API_KEY is required.")

        headers = {"X-API-Key": resolved_api_key}
        self._client = AsyncClient(base_url=normalized_base_url, timeout=timeout, headers=headers)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def status(self) -> ServiceStatusSchema:
        response = await self._client.get("/")
        response.raise_for_status()

        return ServiceStatusSchema.model_validate(response.json())

    async def generate_video(
        self,
        request: VideoGenerationRequestSchema,
        timeout: float | None = None,
    ) -> VideoJobAcceptedSchema:
        payload = request.model_dump(exclude_none=True)
        response = await self._client.post("/video/generate", json=payload, timeout=timeout)
        response.raise_for_status()

        return VideoJobAcceptedSchema.model_validate(response.json())

    async def get_video_job_status(self, job_id: str) -> VideoJobSchema:
        response = await self._client.get(f"/video/jobs/{job_id}")
        response.raise_for_status()

        return VideoJobSchema.model_validate(response.json())

    async def get_video_response(self, video_id: str) -> VideoGenerationResponseSchema:
        response = await self._client.get(f"/video/response/{video_id}")
        response.raise_for_status()

        return VideoGenerationResponseSchema.model_validate(response.json())

    async def download_video(self, video_id: str) -> bytes:
        response = await self._client.get(f"/video/{video_id}", timeout=None)
        response.raise_for_status()

        return response.content


class InstantVideoClient:
    def __init__(self, base_url: str, timeout: float = 1800.0, api_key: str | None = None) -> None:
        normalized_base_url = base_url.rstrip("/")
        resolved_api_key = api_key or os.environ.get("INSTANTVIDEO_API_KEY")

        if not resolved_api_key:
            raise ValueError("INSTANTVIDEO_API_KEY is required.")

        headers = {"X-API-Key": resolved_api_key}
        self._client = Client(base_url=normalized_base_url, timeout=timeout, headers=headers)

    def close(self) -> None:
        self._client.close()

    def status(self) -> ServiceStatusSchema:
        response = self._client.get("/")
        response.raise_for_status()

        return ServiceStatusSchema.model_validate(response.json())

    def generate_video(
        self,
        request: VideoGenerationRequestSchema,
        timeout: float | None = None,
    ) -> VideoJobAcceptedSchema:
        payload = request.model_dump(exclude_none=True)
        response = self._client.post("/video/generate", json=payload, timeout=timeout)
        response.raise_for_status()

        return VideoJobAcceptedSchema.model_validate(response.json())

    def get_video_job_status(self, job_id: str) -> VideoJobSchema:
        response = self._client.get(f"/video/jobs/{job_id}")
        response.raise_for_status()

        return VideoJobSchema.model_validate(response.json())

    def get_video_response(self, video_id: str) -> VideoGenerationResponseSchema:
        response = self._client.get(f"/video/response/{video_id}")
        response.raise_for_status()

        return VideoGenerationResponseSchema.model_validate(response.json())

    def download_video(self, video_id: str) -> bytes:
        response = self._client.get(f"/video/{video_id}", timeout=None)
        response.raise_for_status()

        return response.content
