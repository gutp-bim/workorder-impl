"""
NATS サブジェクト定数 — interfaces.yaml の async-pub-sub IF に対応。

IF-OBS-003  obs.iot-event.created / obs.report.created
IF-ISSUE-002  issue.created / issue.updated / issue.resolved
IF-TICKET-002 ticket.estimate.approved / ticket.status.updated
"""


class OBS:
    IOT_EVENT_CREATED = "obs.iot-event.created"
    REPORT_CREATED = "obs.report.created"


class ISSUE:
    CREATED = "issue.created"
    UPDATED = "issue.updated"
    RESOLVED = "issue.resolved"


class TICKET:
    ESTIMATE_APPROVED = "ticket.estimate.approved"
    STATUS_UPDATED = "ticket.status.updated"
