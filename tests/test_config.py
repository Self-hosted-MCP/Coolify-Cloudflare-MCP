import pytest

from opsmcp import access, config, consent


@pytest.mark.parametrize("value,expected", [("", True), ("1", True), ("enabled", True), ("ON", True), ("yes", True), ("truee", True),
                                            ("0", False), ("false", False), ("no", False), ("off", False), ("OFF", False)])
def test_zero_trust_stays_on_unless_switched_off_in_plain_words(monkeypatch, value, expected):
    monkeypatch.setenv("ACCESS_ENFORCE", value)
    assert config.enforcing() is expected and access.enforcing() is expected


@pytest.mark.parametrize("value,expected", [("", False), ("0", False), ("off", False), ("1", True), ("enabled", True), ("tru", True)])
def test_read_only_turns_on_for_anything_that_is_not_plainly_off(monkeypatch, value, expected):
    monkeypatch.setenv("READ_ONLY", value)
    assert config.read_only() is expected


async def test_a_typo_in_the_zero_trust_switch_does_not_open_the_confirm_page(monkeypatch):
    monkeypatch.setenv("ACCESS_ENFORCE", "enabled")
    assert await access.who({}) is None
