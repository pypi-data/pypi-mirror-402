"""GoXLR Utility API: Tests helpers - Request Models"""
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from ....models.request import Request


@register_fixture
class RequestFactory(ModelFactory[Request]):
    """Request Factory"""

    __model__ = Request

    id = 1
    data = {"key": "value"}


def test_request() -> None:
    """Test Request"""
    model = RequestFactory.build()

    assert isinstance(model, Request)
    assert model.id == 1
    assert model.data == {"key": "value"}
