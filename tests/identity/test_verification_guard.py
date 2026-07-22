import threading

import pytest

from app.identity.verification_guard import PasswordVerificationGuard, VerificationCapacityError


def test_releases_capacity_after_success() -> None:
    guard = PasswordVerificationGuard(1, 0)

    assert guard.run(lambda: True) is True
    assert guard.run(lambda: "next") == "next"


def test_releases_capacity_after_exception() -> None:
    guard = PasswordVerificationGuard(1, 0)

    with pytest.raises(RuntimeError, match="verification failed"):
        guard.run(lambda: (_ for _ in ()).throw(RuntimeError("verification failed")))

    assert guard.run(lambda: "next") == "next"


def test_times_out_and_proceeds_after_capacity_is_released(caplog) -> None:
    guard = PasswordVerificationGuard(1, 0.01)
    entered = threading.Event()
    release = threading.Event()
    holder = threading.Thread(target=lambda: guard.run(lambda: (entered.set(), release.wait())))
    holder.start()
    assert entered.wait(timeout=1)

    with pytest.raises(VerificationCapacityError):
        guard.run(lambda: True)

    assert "password_verification_limiter_timeout" in caplog.text

    release.set()
    holder.join(timeout=1)
    assert not holder.is_alive()
    assert guard.run(lambda: True) is True
