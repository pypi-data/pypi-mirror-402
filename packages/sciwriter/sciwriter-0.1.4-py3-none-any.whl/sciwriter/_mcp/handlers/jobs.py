"""MCP handlers for background job management.

Actions: list, read, cancel, clear
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compile import compile_handler


async def compile_async_handler(arguments: dict[str, Any]) -> str:
    """Handle compile_async tool - start compilation as background job.

    Returns immediately with job_id for tracking.
    """
    from sciwriter._jobs import job_manager

    project_dir = Path(arguments["project_dir"])

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project not found: {project_dir}"}
        )

    # Create job
    job = job_manager.create_job("compile", arguments)

    # Start job in background
    job_manager.start_job(job, compile_handler)

    return json.dumps(
        {
            "success": True,
            "job_id": job.id,
            "status": job.status.value,
            "message": f"Compilation started. Use job tool with action='read' and job_id='{job.id}' to check progress.",
        }
    )


async def job_handler(arguments: dict[str, Any]) -> str:
    """Handle job tool invocation with action dispatch.

    Args:
        arguments: Tool arguments containing:
            - action: Action to perform (required)
            - job_id: Job ID (for read/cancel)
            - status: Filter by status (for list)
            - limit: Max jobs to return (for list)

    Returns:
        JSON string with action results
    """
    action = arguments.get("action")

    if not action:
        return json.dumps({"success": False, "error": "Missing required: action"})

    if action == "list":
        return await _list_jobs(arguments)
    elif action == "read":
        return await _read_job(arguments)
    elif action == "cancel":
        return await _cancel_job(arguments)
    elif action == "clear":
        return await _clear_jobs(arguments)
    else:
        return json.dumps({"success": False, "error": f"Unknown action: {action}"})


async def _list_jobs(arguments: dict[str, Any]) -> str:
    """List all background jobs."""
    from sciwriter._jobs import JobStatus, job_manager

    status_filter = arguments.get("status")
    limit = arguments.get("limit", 20)

    status = JobStatus(status_filter) if status_filter else None
    jobs = job_manager.list_jobs(status=status, limit=limit)

    return json.dumps(
        {"success": True, "jobs": [j.to_dict() for j in jobs], "count": len(jobs)}
    )


async def _read_job(arguments: dict[str, Any]) -> str:
    """Read status of a specific job."""
    from sciwriter._jobs import job_manager

    job_id = arguments.get("job_id")
    if not job_id:
        return json.dumps({"success": False, "error": "Missing required: job_id"})

    job = job_manager.get_job(job_id)
    if not job:
        return json.dumps({"success": False, "error": f"Job not found: {job_id}"})

    return json.dumps({"success": True, **job.to_dict()})


async def _cancel_job(arguments: dict[str, Any]) -> str:
    """Cancel a running job."""
    from sciwriter._jobs import job_manager

    job_id = arguments.get("job_id")
    if not job_id:
        return json.dumps({"success": False, "error": "Missing required: job_id"})

    if job_manager.cancel_job(job_id):
        return json.dumps({"success": True, "message": f"Job {job_id} cancelled"})
    else:
        return json.dumps(
            {
                "success": False,
                "error": f"Cannot cancel job {job_id} (not running or not found)",
            }
        )


async def _clear_jobs(arguments: dict[str, Any]) -> str:
    """Clear completed/failed jobs."""
    from sciwriter._jobs import JobStatus, job_manager

    # Clear completed and failed jobs by default
    statuses = [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    count = job_manager.clear_jobs(statuses)

    return json.dumps(
        {"success": True, "cleared": count, "message": f"Cleared {count} finished jobs"}
    )


__all__ = [
    "compile_async_handler",
    "job_handler",
]
