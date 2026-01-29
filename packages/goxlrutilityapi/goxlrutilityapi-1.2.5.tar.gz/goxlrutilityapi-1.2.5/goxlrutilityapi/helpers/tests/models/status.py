"""GoXLR Utility API: Tests helpers - Status Models"""
from typing import Final

from polyfactory import Fixture
from polyfactory.factories.pydantic_factory import ModelFactory

from ....models.status import Config, Files, Hardware, Mixer, Paths, Status, UsbDevice

FIXTURE_SERIAL: Final[str] = "abc123"
FIXTURE_MANUFACTURER_NAME: Final[str] = "Name of the manufacturer"
FIXTURE_NAME: Final[str] = "Name of the device"


class UsbDeviceFactory(ModelFactory[UsbDevice]):
    """USB Device Factory"""

    __model__ = UsbDevice

    manufacturer_name = FIXTURE_MANUFACTURER_NAME
    product_name = FIXTURE_NAME


class HardwareFactory(ModelFactory[Hardware]):
    """Hardware Factory"""

    __model__ = Hardware

    usb = UsbDeviceFactory().build()


class MixerFactory(ModelFactory[Mixer]):
    """Mixer Factory"""

    __model__ = Mixer

    hardware = HardwareFactory().build()


class StatusFactory(ModelFactory[Status]):
    """Status Factory"""

    __model__ = Status

    config = Fixture(Config)
    mixers = {FIXTURE_SERIAL: MixerFactory().build()}
    paths = Fixture(Paths)
    files = Fixture(Files)


def test_status() -> None:
    """Test Status"""
    model = StatusFactory.build()

    assert isinstance(model, Status)
    assert isinstance(model.config, Config)
    assert isinstance(model.mixers, dict)
    assert isinstance(model.paths, Paths)
    assert isinstance(model.files, Files)
