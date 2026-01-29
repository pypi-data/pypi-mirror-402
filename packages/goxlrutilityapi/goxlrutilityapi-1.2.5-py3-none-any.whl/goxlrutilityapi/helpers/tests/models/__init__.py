"""GoXLR Utility API: Tests helpers - Models"""
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from ....models import DefaultBaseModel


@register_fixture
class DefaultBaseModelFactory(ModelFactory[DefaultBaseModel]):
    """DefaultBaseModel Factory"""

    __model__ = DefaultBaseModel


def test_default_base_model() -> None:
    """Test DefaultBaseModel"""
    model = DefaultBaseModelFactory.build()

    assert isinstance(model, DefaultBaseModel)
