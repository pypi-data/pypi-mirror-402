import re
import pytest

@pytest.mark.parametrize(
    "input, expected",
    [
        pytest.param("Token: abc123", True, id="Valid Token Input"),
        pytest.param("Token: abc234", False, id="Invalid Token Input"),
    ]
)
def test_token_extraction(input: str, expected: bool):
    STATIC_TOKEN = "abc123"
    pattern = re.compile(r"^Token: (\w+)$")
    match = pattern.match(input)
    assert match is not None
    token = match.group(1)
    # if expected is True:
    #     assert token == STATIC_TOKEN
    # else:
    #     assert token != STATIC_TOKEN

