import threading

import pytest

from app.job_analysis.llm_guard import LLMCapacityError, LLMConcurrencyGuard


def test_llm_guard_times_out_and_releases_capacity() -> None:
    guard = LLMConcurrencyGuard(1, 0.01)
    entered = threading.Event()
    release = threading.Event()
    holder = threading.Thread(
        target=lambda: guard.run(lambda: (entered.set(), release.wait()))
    )
    holder.start()
    assert entered.wait(timeout=1)

    with pytest.raises(LLMCapacityError):
        guard.run(lambda: True)

    release.set()
    holder.join(timeout=1)
    assert not holder.is_alive()
    assert guard.run(lambda: "recovered") == "recovered"
