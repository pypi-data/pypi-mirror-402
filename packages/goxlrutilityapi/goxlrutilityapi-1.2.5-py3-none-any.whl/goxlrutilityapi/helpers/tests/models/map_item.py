"""GoXLR Utility API: Tests helpers - MapItem Models"""
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from ....models.map_item import MapItem


@register_fixture
class MapItemFactory(ModelFactory[MapItem]):
    """MapItem Factory"""

    __model__ = MapItem

    name = "Name"
    icon = "mdi:icon"


def test_map_item() -> None:
    """Test MapItem"""
    model = MapItemFactory.build()

    assert isinstance(model, MapItem)
    assert model.name == "Name"
    assert model.icon == "mdi:icon"
