from api_sos.utils import coro


def test_coro():
    @coro
    async def coro_helper(input_: str) -> str:
        return input_

    assert coro_helper("test") == "test"
