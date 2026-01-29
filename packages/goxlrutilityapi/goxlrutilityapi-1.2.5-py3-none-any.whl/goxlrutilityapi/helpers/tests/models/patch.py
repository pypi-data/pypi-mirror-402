"""GoXLR Utility API: Tests helpers - Patch Models"""
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from ....models.patch import Patch


@register_fixture
class PatchFactory(ModelFactory[Patch]):
    """Patch Factory"""

    __model__ = Patch

    op = "op"
    path = "path"
    value = "value"


def test_patch() -> None:
    """Test Patch"""
    model = PatchFactory.build()

    assert isinstance(model, Patch)
    assert model.op == "op"
    assert model.path == "path"
    assert model.value == "value"
