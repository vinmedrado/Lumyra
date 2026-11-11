from __future__ import annotations

import hashlib

import pytest

from services import security_service


def test_new_passwords_use_bcrypt():
    digest = security_service.hash_password("secure-example-password")
    assert digest.startswith("$2")
    assert security_service.verify_password("secure-example-password", digest) is True
    assert security_service.verify_password("incorrect", digest) is False


def test_new_passwords_fail_closed_if_bcrypt_is_unavailable(monkeypatch):
    monkeypatch.setattr(security_service, "_pwd_context", None)
    with pytest.raises(RuntimeError, match="Secure password hashing"):
        security_service.hash_password("sensitive-password")


def test_existing_legacy_sha256_hashes_remain_readable_for_migration():
    # Backward compatibility only; the application must not create new SHA-256 hashes.
    legacy = "sha256$" + hashlib.sha256(b"old-password").hexdigest()
    assert security_service.verify_password("old-password", legacy)
    assert not security_service.verify_password("wrong-password", legacy)
