import asyncio
import logging
from typing import Awaitable, Iterable, cast

import pytest

from lazy_logging import LazyLogger, LazyLoggerFactory


def _make_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.propagate = True
    logger.setLevel(logging.NOTSET)
    return logger


def _messages_for(logger_name: str, records: Iterable[logging.LogRecord]) -> list[str]:
    return [record.getMessage() for record in records if record.name == logger_name]


def test_lazy_logger_logs_with_env_level(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = _make_logger("lazy_logging.test.sync")
    monkeypatch.setenv("LL_LEVEL_TEST", "DEBUG")

    @LazyLogger(logger, "TEST")
    def add(a: int, b: int) -> int:
        return a + b

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        result = add(1, 2)

    assert result == 3
    messages = _messages_for(logger.name, caplog.records)
    assert any("Fetching" in message for message in messages)
    assert any("returns: 3" in message for message in messages)


def test_lazy_logger_factory_key_and_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LL_LEVEL_EXAMPLE", "INFO")
    factory = LazyLoggerFactory("EXAMPLE")
    logger = _make_logger("lazy_logging.test.factory")
    lazy_logger = factory(logger)

    assert lazy_logger.key == "LL_LEVEL_EXAMPLE"
    assert lazy_logger.log_level == logging.INFO


def test_lazy_logger_async_function(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = _make_logger("lazy_logging.test.async")
    monkeypatch.setenv("LL_LEVEL_ASYNC", "DEBUG")

    @LazyLogger(logger, "ASYNC")
    async def work(value: int) -> int:
        await asyncio.sleep(0)
        return value + 1

    async def runner() -> int:
        return await work(2)

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        result = asyncio.run(runner())

    assert result == 3
    messages = _messages_for(logger.name, caplog.records)
    assert any("Fetching" in message for message in messages)
    assert any("returns: 3" in message for message in messages)


def test_lazy_logger_async_descriptor(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = _make_logger("lazy_logging.test.descriptor")
    monkeypatch.setenv("LL_LEVEL_DESC", "DEBUG")
    lazy_logger = LazyLogger(logger, "DESC")

    class AsyncDescriptor:
        async def __get__(self, instance: "Thing", owner: type["Thing"]) -> int:
            await asyncio.sleep(0)
            return instance.value

    descriptor = AsyncDescriptor()
    setattr(descriptor, "__name__", "AsyncDescriptor")

    class Thing:
        data = lazy_logger(descriptor)

        def __init__(self, value: int) -> None:
            self.value = value

    async def runner() -> int:
        thing = Thing(5)
        return await cast(Awaitable[int], thing.data)

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        result = asyncio.run(runner())

    assert result == 5
    messages = _messages_for(logger.name, caplog.records)
    assert any("Fetching" in message for message in messages)
    assert any("returns: 5" in message for message in messages)
