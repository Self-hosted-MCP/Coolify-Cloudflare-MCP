import time

import pytest

from opsmcp import audit, config, confirm_app, consent
from test_consent import make


ME = "test@localhost"     # the fixed identity when Zero Trust is off in tests


def test_nothing_is_on_by_default():
    assert consent.allow_all_until() == 0.0


async def test_tickets_run_with_no_tap_while_it_is_on():
    consent.start_allow_all()
    t, calls = make()
    assert t.status == "approved" and t.decided_by == "allow-all"
    assert (await consent.ENGINE.run_if_approved(t.id)) == ("done", "ran ok") and len(calls) == 1


async def test_high_risk_also_runs_with_no_tap():
    consent.start_allow_all()
    t, calls = make(risk="high")
    assert (await consent.ENGINE.run_if_approved(t.id))[0] == "done"


def test_it_ends_by_itself(monkeypatch):
    consent.start_allow_all()
    real = time.time()
    monkeypatch.setattr(consent.time, "time", lambda: real + 11 * 60)
    assert consent.allow_all_until() == 0.0


def test_after_it_ends_tickets_wait_again(monkeypatch):
    consent.start_allow_all()
    consent._allow_all_until = time.time() - 1
    t, _ = make()
    assert t.status == "pending"


def test_stop_ends_it():
    consent.start_allow_all()
    assert consent.stop_allow_all() is True and consent.allow_all_until() == 0.0
    assert consent.stop_allow_all() is False
    assert make()[0].status == "pending"


def test_freeze_ends_it_and_blocks_new_tickets():
    consent.start_allow_all()
    consent.set_frozen(True)
    assert consent.allow_all_until() == 0.0
    with pytest.raises(consent.ChangesOff):
        make()


def test_cannot_start_while_frozen_or_read_only(monkeypatch):
    consent.set_frozen(True)
    assert consent.start_allow_all() == 0.0
    consent.set_frozen(False)
    monkeypatch.setenv("READ_ONLY", "1")
    assert consent.start_allow_all() == 0.0


def test_minutes_zero_turns_the_feature_off(monkeypatch):
    monkeypatch.setenv("ALLOW_ALL_MINUTES", "0")
    assert consent.start_allow_all() == 0.0
    t, _ = make()
    assert 'approve-all' not in confirm_app.ticket_page("a@b.c", t.id)


def test_default_is_ten_minutes():
    assert config.allow_all_minutes() == 10
    assert 595 < consent.start_allow_all() - time.time() <= 600


def test_pages_show_the_button_and_the_stop():
    t, _ = make()
    assert f"/confirm/{t.id}/approve-all" in confirm_app.ticket_page("a@b.c", t.id)
    consent.start_allow_all()
    html = confirm_app.page("a@b.c")
    assert "ALLOW ALL is on until" in html and "/allow-all/stop" in html


def test_a_typed_word_ticket_has_no_allow_all_button():
    t, _ = make(confirm_word="example.com")
    assert "approve-all" not in confirm_app.ticket_page("a@b.c", t.id)


def _client():
    from starlette.testclient import TestClient
    return TestClient(confirm_app.app(), follow_redirects=False)


def test_approve_all_button_approves_and_starts_the_window():
    t, _ = make()
    r = _client().post(f"/confirm/{t.id}/approve-all", data={"csrf": consent.csrf(t.id, ME)})
    assert r.status_code == 303 and "n=allall" in r.headers["location"]
    assert consent.ENGINE.get(t.id).status == "approved" and consent.allow_all_until() > time.time()


def test_approve_all_needs_the_form_token():
    t, _ = make()
    r = _client().post(f"/confirm/{t.id}/approve-all", data={"csrf": "bad"})
    assert r.status_code == 403 and consent.allow_all_until() == 0.0 and consent.ENGINE.get(t.id).status == "pending"


def test_approve_all_refuses_a_typed_word_ticket():
    t, _ = make(confirm_word="example.com")
    r = _client().post(f"/confirm/{t.id}/approve-all", data={"csrf": consent.csrf(t.id, ME)})
    assert "n=gone" in r.headers["location"] and consent.allow_all_until() == 0.0 and consent.ENGINE.get(t.id).status == "pending"


def test_stop_button():
    consent.start_allow_all()
    r = _client().post("/allow-all/stop", data={"csrf": consent.csrf("allowall", ME)})
    assert "n=allstopped" in r.headers["location"] and consent.allow_all_until() == 0.0


def test_a_stale_window_does_not_leak_between_tests():
    assert consent.allow_all_until() == 0.0
