"""GoXLR Utility API: Status Models"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from . import DefaultBaseModel


@dataclass
class Config(DefaultBaseModel):
    """Config Model"""

    daemon_version: Optional[str] = field(default=None)
    autostart_enabled: Optional[bool] = field(default=None)
    show_tray_icon: Optional[bool] = field(default=None)
    tts_enabled: Optional[bool] = field(default=None)
    allow_network_access: Optional[bool] = field(default=None)
    log_level: Optional[str] = field(default=None)


@dataclass
class Versions(DefaultBaseModel):
    """Versions Model"""

    firmware: Optional[list[int]] = field(default=None)
    fpga_count: Optional[int] = field(default=None)
    dice: Optional[list[int]] = field(default=None)


@dataclass
class UsbDevice(DefaultBaseModel):
    """USB Device Model"""

    manufacturer_name: str
    product_name: str
    version: list[int]
    bus_number: int
    address: int
    identifier: str | None


@dataclass
class Hardware(DefaultBaseModel):
    """Hardware Model"""

    versions: Versions
    serial_number: str
    manufactured_date: str
    device_type: str
    usb_device: UsbDevice


@dataclass
class FaderStatus(DefaultBaseModel):
    """Fader Status Model"""

    channel: str
    mute_type: str
    mute_state: str
    scribble: Optional[Any] = field(default=None)


@dataclass
class FaderStatuses(DefaultBaseModel):
    """Fader Statuses Model"""

    a: FaderStatus = field(metadata={"alias": "A"})
    b: FaderStatus = field(metadata={"alias": "B"})
    c: FaderStatus = field(metadata={"alias": "C"})
    d: FaderStatus = field(metadata={"alias": "D"})


@dataclass
class MicGains(DefaultBaseModel):
    """Mic Gains Model"""

    dynamic: Optional[int] = field(default=None, metadata={"alias": "Dynamic"})
    condenser: Optional[int] = field(default=None, metadata={"alias": "Condenser"})
    jack: Optional[int] = field(default=None, metadata={"alias": "Jack"})


@dataclass
class Gain(DefaultBaseModel):
    """Gain Model"""

    equalizer4_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer4KHz"}
    )
    equalizer16_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer16KHz"}
    )
    equalizer1_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer1KHz"}
    )
    equalizer2_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer2KHz"}
    )
    equalizer125_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer125Hz"}
    )
    equalizer500_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer500Hz"}
    )
    equalizer31_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer31Hz"}
    )
    equalizer63_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer63Hz"}
    )
    equalizer8_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer8KHz"}
    )
    equalizer250_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer250Hz"}
    )


@dataclass
class Frequency(DefaultBaseModel):
    """Frequency Model"""

    equalizer16_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer16KHz"}
    )
    equalizer500_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer500Hz"}
    )
    equalizer125_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer125Hz"}
    )
    equalizer4_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer4KHz"}
    )
    equalizer250_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer250Hz"}
    )
    equalizer8_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer8KHz"}
    )
    equalizer2_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer2KHz"}
    )
    equalizer31_hz: Optional[float] = field(
        default=None, metadata={"alias": "Equalizer31Hz"}
    )
    equalizer1_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer1KHz"}
    )
    equalizer63_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer63Hz"}
    )


@dataclass
class Equaliser(DefaultBaseModel):
    """Equaliser Model"""

    gain: Optional[Gain] = field(default=None)
    frequency: Optional[Frequency] = field(default=None)


@dataclass
class Gain1(DefaultBaseModel):
    """Gain1 Model"""

    equalizer90_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer90Hz"}
    )
    equalizer250_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer250Hz"}
    )
    equalizer1_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer1KHz"}
    )
    equalizer3_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer3KHz"}
    )
    equalizer8_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer8KHz"}
    )
    equalizer500_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer500Hz"}
    )


@dataclass
class Frequency1(DefaultBaseModel):
    """Frequency1 Model"""

    equalizer3_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer3KHz"}
    )
    equalizer1_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer1KHz"}
    )
    equalizer90_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer90Hz"}
    )
    equalizer250_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer250Hz"}
    )
    equalizer8_k_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer8KHz"}
    )
    equalizer500_hz: Optional[int] = field(
        default=None, metadata={"alias": "Equalizer500Hz"}
    )


@dataclass
class EqualiserMini(DefaultBaseModel):
    """Equaliser Mini Model"""

    gain: Optional[Gain1] = field(default=None)
    frequency: Optional[Frequency1] = field(default=None)


@dataclass
class NoiseGate(DefaultBaseModel):
    """Noise Gate Model"""

    threshold: Optional[int] = field(default=None)
    attack: Optional[int] = field(default=None)
    release: Optional[int] = field(default=None)
    enabled: Optional[bool] = field(default=None)
    attenuation: Optional[int] = field(default=None)


@dataclass
class Compressor(DefaultBaseModel):
    """Compressor Model"""

    threshold: Optional[int] = field(default=None)
    ratio: Optional[int] = field(default=None)
    attack: Optional[int] = field(default=None)
    release: Optional[int] = field(default=None)
    makeup_gain: Optional[int] = field(default=None)


@dataclass
class MicStatus(DefaultBaseModel):
    """Mic Status Model"""

    mic_type: Optional[str] = field(default=None)
    mic_gains: Optional[MicGains] = field(default=None)
    equaliser: Optional[Equaliser] = field(default=None)
    equaliser_mini: Optional[EqualiserMini] = field(default=None)
    noise_gate: Optional[NoiseGate] = field(default=None)
    compressor: Optional[Compressor] = field(default=None)


@dataclass
class Volumes(DefaultBaseModel):
    """Volumes Model"""

    mic: int = field(metadata={"alias": "Mic"})
    line_in: int = field(metadata={"alias": "LineIn"})
    console: int = field(metadata={"alias": "Console"})
    system: int = field(metadata={"alias": "System"})
    game: int = field(metadata={"alias": "Game"})
    chat: int = field(metadata={"alias": "Chat"})
    sample: int = field(metadata={"alias": "Sample"})
    music: int = field(metadata={"alias": "Music"})
    headphones: int = field(metadata={"alias": "Headphones"})
    mic_monitor: int = field(metadata={"alias": "MicMonitor"})
    line_out: int = field(metadata={"alias": "LineOut"})


@dataclass
class Levels(DefaultBaseModel):
    """Levels Model"""

    output_monitor: str
    volumes: Volumes
    submix_supported: bool = field(default=None)
    submix: Optional[Any] = field(default=None)
    bleep: Optional[int] = field(default=None)
    deess: Optional[int] = field(default=None)


@dataclass
class RouterItem(DefaultBaseModel):
    """Router Item Model"""

    headphones: Optional[bool] = field(default=None, metadata={"alias": "Headphones"})
    broadcast_mix: Optional[bool] = field(
        default=None, metadata={"alias": "BroadcastMix"}
    )
    chat_mic: Optional[bool] = field(default=None, metadata={"alias": "ChatMic"})
    sampler: Optional[bool] = field(default=None, metadata={"alias": "Sampler"})
    line_out: Optional[bool] = field(default=None, metadata={"alias": "LineOut"})


@dataclass
class Router(DefaultBaseModel):
    """Router Model"""

    microphone: Optional[RouterItem] = field(
        default=None, metadata={"alias": "Microphone"}
    )
    chat: Optional[RouterItem] = field(default=None, metadata={"alias": "Chat"})
    music: Optional[RouterItem] = field(default=None, metadata={"alias": "Music"})
    game: Optional[RouterItem] = field(default=None, metadata={"alias": "Game"})
    console: Optional[RouterItem] = field(default=None, metadata={"alias": "Console"})
    line_in: Optional[RouterItem] = field(default=None, metadata={"alias": "LineIn"})
    system: Optional[RouterItem] = field(default=None, metadata={"alias": "System"})
    samples: Optional[RouterItem] = field(default=None, metadata={"alias": "Samples"})


@dataclass
class CoughButton(DefaultBaseModel):
    """Cough Button Model"""

    is_toggle: Optional[bool] = field(default=None)
    mute_type: Optional[str] = field(default=None)
    state: Optional[str] = field(default=None)


@dataclass
class Colours(DefaultBaseModel):
    """Colours Model"""

    colour_one: Optional[str] = field(default=None)
    colour_two: Optional[str] = field(default=None)


@dataclass
class Fader(DefaultBaseModel):
    """Fader Model"""

    style: Optional[str] = field(default=None)
    colours: Colours = field(default=None)


@dataclass
class Animation(DefaultBaseModel):
    """Animation Model"""

    supported: Optional[bool] = field(default=None)
    mode: Optional[str] = field(default=None)
    mod1: Optional[int] = field(default=None)
    mod2: Optional[int] = field(default=None)
    waterfall_direction: Optional[str] = field(default=None)


@dataclass
class Faders(DefaultBaseModel):
    """Faders Model"""

    a: Fader = field(metadata={"alias": "A"})
    b: Fader = field(metadata={"alias": "B"})
    c: Fader = field(metadata={"alias": "C"})
    d: Fader = field(metadata={"alias": "D"})


@dataclass
class Button(DefaultBaseModel):
    """Button Model"""

    off_style: Optional[str]
    colours: Colours


@dataclass
class Buttons(DefaultBaseModel):
    """Buttons Model"""

    bleep: Button = field(metadata={"alias": "Bleep"})
    cough: Button = field(metadata={"alias": "Cough"})
    fader1_mute: Button = field(metadata={"alias": "Fader1Mute"})
    fader2_mute: Button = field(metadata={"alias": "Fader2Mute"})
    fader3_mute: Button = field(metadata={"alias": "Fader3Mute"})
    fader4_mute: Button = field(metadata={"alias": "Fader4Mute"})


@dataclass
class Global(DefaultBaseModel):
    """Global Model"""

    colour_one: Optional[str]


@dataclass
class Accent(DefaultBaseModel):
    """Accent Model"""

    colour_one: Optional[str]


@dataclass
class Simple(DefaultBaseModel):
    """Simple Model"""

    global_: Optional[Global] = field(default=None, metadata={"alias": "Global"})
    accent: Accent = field(default=None, metadata={"alias": "Accent"})


@dataclass
class Lighting(DefaultBaseModel):
    """Lighting Model"""

    animation: Animation
    faders: Faders
    buttons: Buttons
    simple: Simple
    sampler: Optional[dict[str, Any]] = field(default=None)
    encoders: Optional[dict[str, Any]] = field(default=None)


@dataclass
class Display(DefaultBaseModel):
    """Display Model"""

    gate: Optional[str]
    compressor: Optional[str]
    equaliser: Optional[str]
    equaliser_fine: Optional[str]


@dataclass
class Settings(DefaultBaseModel):
    """Settings Model"""

    display: Optional[Display]
    mute_hold_duration: Optional[int]
    vc_mute_also_mute_cm: Optional[bool]


@dataclass
class ButtonDown(DefaultBaseModel):
    """Button Down Model"""

    bleep: Optional[bool] = field(default=None, metadata={"alias": "Bleep"})
    cough: Optional[bool] = field(default=None, metadata={"alias": "Cough"})
    effect_fx: Optional[bool] = field(default=None, metadata={"alias": "EffectFx"})
    effect_hard_tune: Optional[bool] = field(
        default=None, metadata={"alias": "EffectHardTune"}
    )
    effect_megaphone: Optional[bool] = field(
        default=None, metadata={"alias": "EffectMegaphone"}
    )
    effect_robot: Optional[bool] = field(
        default=None, metadata={"alias": "EffectRobot"}
    )
    effect_select1: Optional[bool] = field(
        default=None, metadata={"alias": "EffectSelect1"}
    )
    effect_select2: Optional[bool] = field(
        default=None, metadata={"alias": "EffectSelect2"}
    )
    effect_select3: Optional[bool] = field(
        default=None, metadata={"alias": "EffectSelect3"}
    )
    effect_select4: Optional[bool] = field(
        default=None, metadata={"alias": "EffectSelect4"}
    )
    effect_select5: Optional[bool] = field(
        default=None, metadata={"alias": "EffectSelect5"}
    )
    effect_select6: Optional[bool] = field(
        default=None, metadata={"alias": "EffectSelect6"}
    )
    fader1_mute: Optional[bool] = field(default=None, metadata={"alias": "Fader1Mute"})
    fader2_mute: Optional[bool] = field(default=None, metadata={"alias": "Fader2Mute"})
    fader3_mute: Optional[bool] = field(default=None, metadata={"alias": "Fader3Mute"})
    fader4_mute: Optional[bool] = field(default=None, metadata={"alias": "Fader4Mute"})
    sampler_bottom_left: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerBottomLeft"}
    )
    sampler_bottom_right: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerBottomRight"}
    )
    sampler_clear: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerClear"}
    )
    sampler_select_a: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerSelectA"}
    )
    sampler_select_b: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerSelectB"}
    )
    sampler_select_c: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerSelectC"}
    )
    sampler_top_left: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerTopLeft"}
    )
    sampler_top_right: Optional[bool] = field(
        default=None, metadata={"alias": "SamplerTopRight"}
    )


@dataclass
class Mixer(DefaultBaseModel):
    """Mixer Model"""

    hardware: Hardware
    shutdown_commands: list[Any]
    fader_status: FaderStatuses
    mic_status: MicStatus
    levels: Levels
    router: Router
    cough_button: CoughButton
    lighting: Lighting
    effects: Any
    sampler: Any
    settings: Settings
    button_down: ButtonDown
    profile_name: str
    mic_profile_name: str


@dataclass
class Paths(DefaultBaseModel):
    """Paths Model"""

    profile_directory: Optional[str]
    mic_profile_directory: Optional[str]
    samples_directory: Optional[str]
    presets_directory: Optional[str]
    icons_directory: Optional[str]


@dataclass
class Files(DefaultBaseModel):
    """Files Model"""

    profiles: list[str]
    mic_profiles: list[str]
    presets: list[str]
    samples: dict[str, Any]
    icons: list[str]


@dataclass
class StatusData(DefaultBaseModel):
    """Status Data Model"""

    config: Config
    mixers: dict[str, Mixer]
    paths: Paths
    files: Files


@dataclass
class Data(DefaultBaseModel):
    """Data Model"""

    status: StatusData = field(metadata={"alias": "Status"})


@dataclass
class Status:
    """GoXLR Utility API: Status Model"""

    id: str
    status: str
    data: dict[str, Any]
    jsonrpc: str = "2.0"
    error: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
