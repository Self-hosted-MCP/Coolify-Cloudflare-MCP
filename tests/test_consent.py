import asyncio

import pytest

from opsmcp import audit, consent


def make(tool="t", counter=None, payload=None, **kw):
    counter = counter if counter is not None else []

    async def run(p, secret):
        counter.append(1)
        return "ran ok"
    return consent.ENGINE.create(tool, kw.pop("summary", "Do the thing"), payload or {"a": 1}, run, **kw), counter


async def test_nothing_runs_before_the_tap():
    t, calls = make()
    assert (await consent.ENGINE.run_if_approved(t.id))[0] == "pending" and calls == []


async def test_runs_once_after_approval_and_never_twice():
    t, calls = make()
    consent.ENGINE.decide(t.id, True, "owner@example.com")
    first = await consent.ENGINE.run_if_approved(t.id)
    second = await consent.ENGINE.run_if_approved(t.id)
    assert first == ("done", "ran ok") and second[0] == "done" and len(calls) == 1


async def test_two_runners_at_once_still_run_once():
    t, calls = make()
    consent.ENGINE.decide(t.id, True, "a@b.c")
    await asyncio.gather(*[consent.ENGINE.run_if_approved(t.id) for _ in range(5)])
    assert len(calls) == 1


async def test_denied_never_runs():
    t, calls = make()
    consent.ENGINE.decide(t.id, False, "a@b.c")
    assert (await consent.ENGINE.run_if_approved(t.id))[0] == "denied" and calls == []
    with pytest.raises(consent.ConsentError):
        consent.ENGINE.decide(t.id, True, "a@b.c")     # a denied ticket cannot be approved afterwards


async def test_expired_ticket_cannot_be_approved_or_run(monkeypatch):
    monkeypatch.setenv("CONFIRM_TTL_SECONDS", "0")
    t, calls = make()
    await asyncio.sleep(0.05)
    with pytest.raises(consent.ConsentError):
        consent.ENGINE.decide(t.id, True, "a@b.c")
    assert (await consent.ENGINE.run_if_approved(t.id))[0] == "expired" and calls == []


async def test_changed_arguments_after_approval_are_refused():
    t, calls = make(payload={"id": "one"})
    consent.ENGINE.decide(t.id, True, "a@b.c")
    t.payload["id"] = "two"                         # someone edits what was approved
    state, text = await consent.ENGINE.run_if_approved(t.id)
    assert state == "failed" and "changed" in text and calls == []


def test_freeze_and_read_only_stop_new_tickets(monkeypatch):
    consent.set_frozen(True)
    with pytest.raises(consent.ConsentError, match="frozen"):
        make()
    consent.set_frozen(False)
    monkeypatch.setenv("READ_ONLY", "1")
    with pytest.raises(consent.ConsentError, match="read-only"):
        make()


def test_limits_on_open_tickets_and_rate(monkeypatch):
    for _ in range(consent.MAX_OPEN):
        make()
    with pytest.raises(consent.ConsentError, match="several"):
        make()
    consent.ENGINE = consent.Engine()
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    for t in [make()[0], make()[0]]:
        consent.ENGINE.decide(t.id, False, "x")
    with pytest.raises(consent.ConsentError, match="Too many"):
        make()


async def test_executor_errors_become_short_safe_text():
    async def boom(p, secret):
        raise RuntimeError("secret detail token=abc123456789")
    t = consent.ENGINE.create("t", "s", {}, boom)
    consent.ENGINE.decide(t.id, True, "a@b.c")
    state, text = await consent.ENGINE.run_if_approved(t.id)
    assert state == "failed" and "abc123456789" not in text


async def test_waiting_hands_back_a_ticket_when_no_tap_comes():
    t, calls = make()
    out = await consent.ENGINE.wait_and_run(t, 1, "https://confirm.test/confirm")
    assert "Nothing has been done yet" in out and t.id in out and "ops_result" in out and calls == []


def test_form_tokens_are_tied_to_person_and_ticket():
    tok = consent.csrf("T1", "owner@example.com")
    assert consent.csrf_ok("T1", "owner@example.com", tok)
    assert not consent.csrf_ok("T2", "owner@example.com", tok) and not consent.csrf_ok("T1", "other@example.com", tok)
    assert not consent.csrf_ok("T1", "owner@example.com", "") and not consent.csrf_ok("T1", "owner@example.com", None)


def test_the_action_log_hides_secret_shapes_and_is_capped(monkeypatch):
    audit.log("asked", summary="set TOKEN=supersecretvalue99 now", n=3)
    assert "supersecretvalue99" not in "\n".join(audit.recent())
    monkeypatch.setenv("ACTION_LOG_MAX_MB", "0")
    for i in range(20):
        audit.log("x", i=i)
    assert audit.log_file().stat().st_size < 2000


async def test_freeze_after_the_tap_still_stops_the_change():
    t, calls = make()
    consent.ENGINE.decide(t.id, True, "a@b.c")
    consent.set_frozen(True)
    state, text = await consent.ENGINE.run_if_approved(t.id)
    assert state == "denied" and "frozen" in text and calls == []


def test_freezing_cancels_every_open_ticket_and_blocks_new_taps():
    a, _ = make()
    b, _ = make()
    consent.ENGINE.decide(b.id, True, "a@b.c")
    assert consent.ENGINE.cancel_all("frozen") == 2
    assert {consent.ENGINE.get(a.id).status, consent.ENGINE.get(b.id).status} == {"denied"}
    c, _ = make()
    consent.set_frozen(True)
    with pytest.raises(consent.ConsentError, match="frozen"):
        consent.ENGINE.decide(c.id, True, "a@b.c")


def test_read_only_switched_on_after_asking_blocks_the_tap(monkeypatch):
    t, _ = make()
    monkeypatch.setenv("READ_ONLY", "yes please")
    with pytest.raises(consent.ConsentError):
        consent.ENGINE.decide(t.id, True, "a@b.c")


async def test_a_cut_off_call_marks_the_ticket_unknown_and_it_never_runs_again():
    async def cut(p, secret):
        raise asyncio.CancelledError()
    t = consent.ENGINE.create("t", "s", {}, cut)
    consent.ENGINE.decide(t.id, True, "a@b.c")
    with pytest.raises(asyncio.CancelledError):
        await consent.ENGINE.run_if_approved(t.id)
    state, text = await consent.ENGINE.run_if_approved(t.id)
    assert state == "failed" and "unknown" in text


async def test_the_runner_gets_the_checked_payload_and_the_secret_only():
    got = {}

    async def run(p, secret):
        got.update(p=p, secret=secret)
        return "ok"
    t = consent.ENGINE.create("t", "s", {"id": "x"}, run, secret="hidden-value", detail="fingerprint")
    consent.ENGINE.decide(t.id, True, "a@b.c")
    await consent.ENGINE.run_if_approved(t.id)
    assert got == {"p": {"id": "x"}, "secret": "hidden-value"}
    assert "hidden-value" not in "\n".join(audit.recent(50)) and "hidden-value" not in repr(t)
