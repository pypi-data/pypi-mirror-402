from __future__ import annotations

from logsentry_agent.normalizers.windows_eventlog import normalize_event


def test_normalize_login_failed():
    record = {
        "event_id": 4625,
        "channel": "Security",
        "provider": "Microsoft-Windows-Security-Auditing",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "message": "Account Name: bob\nSource Network Address: 10.0.0.5",
        "computer": "WIN-01",
    }
    event = normalize_event(record)
    assert event["action"] == "auth.login_failed"
    assert event["category"] == "authentication"
    assert event["actor_user"] == "bob"
    assert event["actor_ip"] == "10.0.0.5"


def test_normalize_service_install():
    record = {
        "event_id": 7045,
        "channel": "System",
        "provider": "Service Control Manager",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "message": "Service Name: ExampleSvc\nService File Name: C:\\Example.exe",
        "computer": "WIN-01",
    }
    event = normalize_event(record)
    assert event["action"] == "system.service_installed"
    assert event["service"] == "ExampleSvc"
