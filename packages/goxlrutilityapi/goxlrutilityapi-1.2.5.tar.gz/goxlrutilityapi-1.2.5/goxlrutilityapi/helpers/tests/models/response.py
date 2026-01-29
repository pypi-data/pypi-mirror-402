"""GoXLR Utility API: Tests helpers - Response Models"""
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from ....models.response import Response


@register_fixture
class ResponseFactory(ModelFactory[Response]):
    """Response Factory"""

    __model__ = Response

    id = 1
    type = "type"
    data = {"key": "value"}


def test_response() -> None:
    """Test Response"""
    model = ResponseFactory.build()

    assert isinstance(model, Response)
    assert model.id == 1
    assert model.type == "type"
    assert model.data == {"key": "value"}
