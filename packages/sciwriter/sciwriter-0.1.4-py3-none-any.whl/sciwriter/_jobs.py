"""Background job management for long-running MCP operations.

Provides async job support for compilation tasks that may take a long time.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobStatus(Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Represents a background job."""

    id: str
    job_type: str
    arguments: dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None
    progress: int = 0  # 0-100
    progress_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "error": self.error,
            "has_result": self.result is not None,
        }


class JobManager:
    """Manages background jobs for MCP operations."""

    _instance: JobManager | None = None
    _jobs: dict[str, Job]
    _tasks: dict[str, asyncio.Task]

    def __new__(cls) -> JobManager:
        """Singleton pattern for job manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._jobs = {}
            cls._instance._tasks = {}
        return cls._instance

    def create_job(self, job_type: str, arguments: dict[str, Any]) -> Job:
        """Create a new job."""
        job_id = str(uuid.uuid4())[:8]
        job = Job(id=job_id, job_type=job_type, arguments=arguments)
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def list_jobs(self, status: JobStatus | None = None, limit: int = 20) -> list[Job]:
        """List jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    async def run_job(self, job: Job, handler: Any) -> None:
        """Run a job with the given handler."""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()

        try:
            result = await handler(job.arguments)
            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 100
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.error = "Job was cancelled"
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            job.completed_at = datetime.now()

    def start_job(self, job: Job, handler: Any) -> None:
        """Start a job in the background."""
        task = asyncio.create_task(self.run_job(job, handler))
        self._tasks[job.id] = task

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job = self._jobs.get(job_id)
        task = self._tasks.get(job_id)

        if not job or not task:
            return False

        if job.status == JobStatus.RUNNING:
            task.cancel()
            return True
        return False

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove completed/failed jobs older than max_age_hours."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []

        for job_id, job in self._jobs.items():
            if job.status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            ):
                if job.completed_at and job.completed_at < cutoff:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]
            self._tasks.pop(job_id, None)

        return len(to_remove)

    def clear_jobs(self, statuses: list[JobStatus] | None = None) -> int:
        """Clear jobs by status. If statuses is None, clear all finished jobs."""
        if statuses is None:
            statuses = [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

        to_remove = []
        for job_id, job in self._jobs.items():
            if job.status in statuses:
                # Don't clear running jobs
                if job.status != JobStatus.RUNNING:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]
            self._tasks.pop(job_id, None)

        return len(to_remove)


# Global job manager instance
job_manager = JobManager()


__all__ = ["Job", "JobStatus", "JobManager", "job_manager"]
