"""Property 17: MQTT credential validation.

Feature: hestia, Property 17: MQTT credential validation

For any username/password pair, MQTT authentication should succeed if
and only if the credentials match a valid entry in the Hub's user directory.

Validates: Requirements 10.6
"""

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from shared.auth import MQTTCredentialStore

_usernames = st.text(min_size=1, max_size=30, alphabet=st.characters(min_codepoint=48, max_codepoint=122))
_passwords = st.text(min_size=1, max_size=50)


@given(username=_usernames, password=_passwords)
@settings(max_examples=100)
def test_registered_user_authenticates(username: str, password: str) -> None:
    store = MQTTCredentialStore()
    store.add_user(username, password)
    assert store.authenticate(username, password) is True


@given(username=_usernames, password=_passwords, wrong=_passwords)
@settings(max_examples=100)
def test_wrong_password_rejected(username: str, password: str, wrong: str) -> None:
    assume(password != wrong)
    store = MQTTCredentialStore()
    store.add_user(username, password)
    assert store.authenticate(username, wrong) is False


@given(username=_usernames, password=_passwords)
@settings(max_examples=100)
def test_unregistered_user_rejected(username: str, password: str) -> None:
    store = MQTTCredentialStore()
    assert store.authenticate(username, password) is False


@given(username=_usernames, password=_passwords)
@settings(max_examples=100)
def test_removed_user_rejected(username: str, password: str) -> None:
    store = MQTTCredentialStore()
    store.add_user(username, password)
    store.remove_user(username)
    assert store.authenticate(username, password) is False
