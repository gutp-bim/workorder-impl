"""IF-ISSUE-001 — Issue 管理 (from issue_manager)"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException
from gutp.schemas.issue import Issue, IssueCreate, IssueStatus
from pydantic import BaseModel

from .. import state

router = APIRouter(tags=["issues"])


class ReviewBody(BaseModel):
    action: Literal["accept", "reject"]


@router.post("/issues", status_code=201)
async def create_issue(body: IssueCreate) -> Issue:
    record = Issue(issue_id=str(uuid.uuid4()), **body.model_dump())
    state.issues[record.issue_id] = record
    return record


@router.get("/issues/{issue_id}")
async def get_issue(issue_id: str) -> Issue:
    record = state.issues.get(issue_id)
    if not record:
        raise HTTPException(404, detail="Issue not found")
    return record


@router.get("/issues")
async def list_issues() -> list[Issue]:
    return list(state.issues.values())


@router.patch("/issues/{issue_id}/review")
async def review_issue(issue_id: str, body: ReviewBody) -> Issue:
    record = state.issues.get(issue_id)
    if not record:
        raise HTTPException(404, detail="Issue not found")
    if record.issue_status == IssueStatus.RESOLVED:
        raise HTTPException(409, detail="Cannot review a Resolved issue")
    record.issue_status = IssueStatus.UNDER_REVIEW if body.action == "accept" else IssueStatus.OPEN
    return record


@router.patch("/issues/{issue_id}/resolve")
async def resolve_issue(issue_id: str) -> Issue:
    record = state.issues.get(issue_id)
    if not record:
        raise HTTPException(404, detail="Issue not found")
    if record.issue_status != IssueStatus.RESOLVED:
        record.issue_status = IssueStatus.RESOLVED
    return record
