"""Property 11: Storage share access control.

Feature: hestia, Property 11: Storage share access control

For any user and storage share combination, access should be granted
if and only if the user's ID appears in the share's allowed_users list
or the user has the admin role.

Validates: Requirements 5.5
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.samba import SambaManager, SambaShare

_users = st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
_user_lists = st.lists(_users, min_size=0, max_size=5)


@given(user_id=_users, allowed=_user_lists, role=st.sampled_from(["admin", "user"]))
@settings(max_examples=200)
def test_access_control(user_id: str, allowed: list[str], role: str):
    mgr = SambaManager()
    mgr.create_share(SambaShare(name="test", path="/data/test", allowed_users=allowed))

    result = mgr.check_access("test", user_id, role)

    if role == "admin":
        assert result is True
    else:
        assert result == (user_id in allowed)


@given(user_id=_users, role=st.sampled_from(["admin", "user"]))
@settings(max_examples=50)
def test_nonexistent_share_denied(user_id: str, role: str):
    mgr = SambaManager()
    if role != "admin":
        assert mgr.check_access("nonexistent", user_id, role) is False
