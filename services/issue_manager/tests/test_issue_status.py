"""Slice 3: IssueStatus 状態遷移 + obs.report.evaluated 購読のテスト。"""

from __future__ import annotations

ISSUE_BODY = {
    "title": "空調異常",
    "issue_type": "FacilityAsset",
    "derived_from_id": "report-123",
    "derived_from_type": "Report",
    "is_standard": True,
}


async def _make_issue(ac, derived_from_id: str = "report-123") -> dict:
    body = {**ISSUE_BODY, "derived_from_id": derived_from_id}
    resp = await ac.post("/issues", json=body)
    assert resp.status_code == 201
    return resp.json()


# ── デフォルト status ──────────────────────────────────────────────────────────

async def test_issue_created_with_open_status(ac):
    """新規 Issue の issue_status は Open。"""
    data = await _make_issue(ac)
    assert data["issue_status"] == "Open"


# ── obs.report.evaluated ──────────────────────────────────────────────────────

async def test_report_evaluated_sets_pending_review(ac):
    """_handle_report_evaluated 呼び出しで該当 Issue が PendingReview に遷移する。"""
    import gutp_issue_manager.main as m

    data = await _make_issue(ac, derived_from_id="report-999")
    issue_id = data["issue_id"]

    await m._handle_report_evaluated("report-999")

    assert m._issues[issue_id].issue_status == "PendingReview"


async def test_report_evaluated_unknown_report_is_noop(ac):
    """不明な report_id では Issue の status が変化しない。"""
    import gutp_issue_manager.main as m

    data = await _make_issue(ac, derived_from_id="report-abc")
    issue_id = data["issue_id"]

    await m._handle_report_evaluated("report-unknown")

    assert m._issues[issue_id].issue_status == "Open"


# ── /review エンドポイント ────────────────────────────────────────────────────

async def test_review_accept_transitions_to_under_review(ac):
    """accept アクションで PendingReview → UnderReview。"""
    import gutp_issue_manager.main as m

    data = await _make_issue(ac)
    issue_id = data["issue_id"]
    m._issues[issue_id].issue_status = "PendingReview"

    resp = await ac.patch(f"/issues/{issue_id}/review", json={"action": "accept"})
    assert resp.status_code == 200
    assert resp.json()["issue_status"] == "UnderReview"


async def test_review_reject_transitions_to_open(ac):
    """reject アクションで PendingReview → Open。"""
    import gutp_issue_manager.main as m

    data = await _make_issue(ac)
    issue_id = data["issue_id"]
    m._issues[issue_id].issue_status = "PendingReview"

    resp = await ac.patch(f"/issues/{issue_id}/review", json={"action": "reject"})
    assert resp.status_code == 200
    assert resp.json()["issue_status"] == "Open"


async def test_review_nonexistent_issue(ac):
    """存在しない Issue の review は 404。"""
    resp = await ac.patch("/issues/nonexistent/review", json={"action": "accept"})
    assert resp.status_code == 404


# ── /resolve エンドポイント ───────────────────────────────────────────────────

async def test_resolve_sets_resolved_status(ac):
    """resolve で issue_status が Resolved になる。"""
    data = await _make_issue(ac)
    issue_id = data["issue_id"]

    resp = await ac.patch(f"/issues/{issue_id}/resolve")
    assert resp.status_code == 200
    assert resp.json()["issue_status"] == "Resolved"


async def test_resolve_publishes_issue_resolved(ac, mock_nc):
    """resolve 時に issue.resolved が NATS publish される。"""
    import gutp_issue_manager.main as m
    from gutp.events.subjects import ISSUE

    data = await _make_issue(ac)
    issue_id = data["issue_id"]

    m._nc = mock_nc
    await ac.patch(f"/issues/{issue_id}/resolve")

    mock_nc.publish.assert_awaited_once()
    subject = mock_nc.publish.call_args[0][0]
    assert subject == ISSUE.RESOLVED


# ── GET /issues ───────────────────────────────────────────────────────────────

async def test_list_issues_includes_status(ac):
    """GET /issues の全件に issue_status フィールドが含まれる。"""
    await _make_issue(ac, derived_from_id="report-1")
    await _make_issue(ac, derived_from_id="report-2")

    resp = await ac.get("/issues")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    for item in items:
        assert "issue_status" in item
