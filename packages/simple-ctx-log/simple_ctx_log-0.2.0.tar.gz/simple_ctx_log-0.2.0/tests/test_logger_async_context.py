import asyncio
from simple_ctx_log import Logger


def test_async_context_propagation(capsys):
    logger = Logger()

    async def inner():
        logger.log("Inside async task")

    async def outer():
        async with logger.context(request_id=123):
            await inner()

    asyncio.run(outer())
    output = capsys.readouterr().out

    assert "request_id=123" in output
    assert "Inside async task" in output
