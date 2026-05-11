"""Tests for recovery service contracts."""

from src.services.recovery_service import NoopRecoveryService, RecoveryService


def test_noop_recovery_service_is_explicitly_non_persistent():
    service = NoopRecoveryService()

    assert service.supports_persistence is False
    assert service.create_session(form_data={}) is None
    assert service.get_session("missing") is None
    assert service.get_checkpoints("missing") == []


def test_recovery_service_advertises_persistence():
    assert RecoveryService.supports_persistence is True
