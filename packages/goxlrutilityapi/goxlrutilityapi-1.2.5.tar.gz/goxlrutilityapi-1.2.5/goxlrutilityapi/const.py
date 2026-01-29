"""GoXLR Utility API: Constants"""

from typing import Any, Final

from .models.map_item import MapItem
from .models.patch import Patch
from .models.request import Request
from .models.response import Response
from .models.status import Status

# Connection
DEFAULT_HOST: Final[str] = "localhost"
DEFAULT_PORT: Final[int] = 14564

# Mixer
ACCENT: Final[str] = "Accent"
MUTED_STATE: Final[str] = "MutedToX"
UNMUTED_STATE: Final[str] = "Unmuted"
VOLUME_MAX: Final[int] = 255

# Request/Response Keys
KEY_DATA: Final[str] = "data"
KEY_ID: Final[str] = "id"
KEY_TYPE: Final[str] = "type"

# Request Types (https://github.com/GoXLR-on-Linux/goxlr-utility/blob/c2c876dd83ddcd4681b1a674c5cb975796726dd8/ipc/src/lib.rs#L20)
REQUEST_TYPE_COMMAND: Final[str] = "Command"
REQUEST_TYPE_GET_HTTP_STATE: Final[str] = "GetHttpState"
REQUEST_TYPE_GET_STATUS: Final[str] = "GetStatus"
REQUEST_TYPE_OPEN_PATH: Final[str] = "OpenPath"
REQUEST_TYPE_OPEN_UI: Final[str] = "OpenUi"
REQUEST_TYPE_PING: Final[str] = "Ping"
REQUEST_TYPE_RECOVER_DEFAULTS: Final[str] = "RecoverDefaults"
REQUEST_TYPE_SET_AUTOSTART_ENABLED: Final[str] = "SetAutoStartEnabled"
REQUEST_TYPE_SET_SHOW_TRAY_ICON: Final[str] = "SetShowTrayIcon"
REQUEST_TYPE_SET_TTS_ENABLED: Final[str] = "SetTTSEnabled"
REQUEST_TYPE_STOP_DAEMON: Final[str] = "StopDaemon"

# Response Types (https://github.com/GoXLR-on-Linux/goxlr-utility/blob/c2c876dd83ddcd4681b1a674c5cb975796726dd8/ipc/src/lib.rs#L35)
RESPONSE_TYPE_ERROR: Final[str] = "Error"
RESPONSE_TYPE_HTTP_STATE: Final[str] = "HttpState"
RESPONSE_TYPE_OK: Final[str] = "Ok"
RESPONSE_TYPE_PATCH: Final[str] = "Patch"
RESPONSE_TYPE_STATUS: Final[str] = "Status"

# Command Types (https://github.com/GoXLR-on-Linux/goxlr-utility/blob/c2c876dd83ddcd4681b1a674c5cb975796726dd8/ipc/src/lib.rs#LL65C17-L65C17)
COMMAND_TYPE_LOAD_PROFILE_COLOURS: Final[str] = "LoadProfileColours"
COMMAND_TYPE_LOAD_PROFILE: Final[str] = "LoadProfile"
COMMAND_TYPE_SET_ALL_FADER_COLOURS: Final[str] = "SetAllFaderColours"
COMMAND_TYPE_SET_ALL_FADER_DISPLAY_STYLE: Final[str] = "SetAllFaderDisplayStyle"
COMMAND_TYPE_SET_BUTTON_COLOURS: Final[str] = "SetButtonColours"
COMMAND_TYPE_SET_BUTTON_GROUP_COLOURS: Final[str] = "SetButtonGroupColours"
COMMAND_TYPE_SET_BUTTON_GROUP_OFF_STYLE: Final[str] = "SetButtonGroupOffStyle"
COMMAND_TYPE_SET_BUTTON_OFF_STYLE: Final[str] = "SetButtonOffStyle"
COMMAND_TYPE_SET_ENCODER_COLOUR: Final[str] = "SetEncoderColour"
COMMAND_TYPE_SET_FADER_COLOURS: Final[str] = "SetFaderColours"
COMMAND_TYPE_SET_FADER_DISPLAY_STYLE: Final[str] = "SetFaderDisplayStyle"
COMMAND_TYPE_SET_MUTE_STATE: Final[str] = "SetFaderMuteState"
COMMAND_TYPE_SET_SAMPLE_COLOUR: Final[str] = "SetSampleColour"
COMMAND_TYPE_SET_SAMPLE_OFF_STYLE: Final[str] = "SetSampleOffStyle"
COMMAND_TYPE_SET_SIMPLE_COLOUR: Final[str] = "SetSimpleColour"
COMMAND_TYPE_SET_VOLUME: Final[str] = "SetVolume"

# Buttons
BUTTON_BLEEP: Final[str] = "Bleep"
BUTTON_COUGH: Final[str] = "Cough"
BUTTON_EFFECT_FX: Final[str] = "EffectFx"
BUTTON_EFFECT_HARD_TUNE: Final[str] = "EffectHardTune"
BUTTON_EFFECT_MEGAPHONE: Final[str] = "EffectMegaphone"
BUTTON_EFFECT_ROBOT: Final[str] = "EffectRobot"
BUTTON_EFFECT_SELECT_1: Final[str] = "EffectSelect1"
BUTTON_EFFECT_SELECT_2: Final[str] = "EffectSelect2"
BUTTON_EFFECT_SELECT_3: Final[str] = "EffectSelect3"
BUTTON_EFFECT_SELECT_4: Final[str] = "EffectSelect4"
BUTTON_EFFECT_SELECT_5: Final[str] = "EffectSelect5"
BUTTON_EFFECT_SELECT_6: Final[str] = "EffectSelect6"
BUTTON_FADER_1_MUTE: Final[str] = "Fader1Mute"
BUTTON_FADER_2_MUTE: Final[str] = "Fader2Mute"
BUTTON_FADER_3_MUTE: Final[str] = "Fader3Mute"
BUTTON_FADER_4_MUTE: Final[str] = "Fader4Mute"
BUTTON_SAMPLER_BOTTOM_LEFT: Final[str] = "SamplerBottomLeft"
BUTTON_SAMPLER_BOTTOM_RIGHT: Final[str] = "SamplerBottomRight"
BUTTON_SAMPLER_CLEAR: Final[str] = "SamplerClear"
BUTTON_SAMPLER_SELECT_A: Final[str] = "SamplerSelectA"
BUTTON_SAMPLER_SELECT_B: Final[str] = "SamplerSelectB"
BUTTON_SAMPLER_SELECT_C: Final[str] = "SamplerSelectC"
BUTTON_SAMPLER_TOP_LEFT: Final[str] = "SamplerTopLeft"
BUTTON_SAMPLER_TOP_RIGHT: Final[str] = "SamplerTopRight"

# Faders
FADER_A: Final[str] = "A"
FADER_B: Final[str] = "B"
FADER_C: Final[str] = "C"
FADER_D: Final[str] = "D"

# Models
# pylint: disable=invalid-name
MODEL_PATCH: type[Patch] = Patch
MODEL_REQUEST: type[Request] = Request
MODEL_RESPONSE: type[Response[Any]] = Response
MODEL_STATUS: type[Status] = Status
# pylint: enable=invalid-name

MODEL_MAP: Final[dict[str, Any]] = {
    RESPONSE_TYPE_PATCH: MODEL_PATCH,
    RESPONSE_TYPE_STATUS: MODEL_STATUS,
}

KEY_MAP: Final[dict[str, str]] = {
    "a": FADER_A,
    "b": FADER_B,
    "bleep": BUTTON_BLEEP,
    "c": FADER_C,
    "cough": BUTTON_COUGH,
    "d": FADER_D,
    "effect_fx": BUTTON_EFFECT_FX,
    "effect_hard_tune": BUTTON_EFFECT_HARD_TUNE,
    "effect_megaphone": BUTTON_EFFECT_MEGAPHONE,
    "effect_robot": BUTTON_EFFECT_ROBOT,
    "effect_select_1": BUTTON_EFFECT_SELECT_1,
    "effect_select_2": BUTTON_EFFECT_SELECT_2,
    "effect_select_3": BUTTON_EFFECT_SELECT_3,
    "effect_select_4": BUTTON_EFFECT_SELECT_4,
    "effect_select_5": BUTTON_EFFECT_SELECT_5,
    "effect_select_6": BUTTON_EFFECT_SELECT_6,
    "fader1_mute": BUTTON_FADER_1_MUTE,
    "fader2_mute": BUTTON_FADER_2_MUTE,
    "fader3_mute": BUTTON_FADER_3_MUTE,
    "fader4_mute": BUTTON_FADER_4_MUTE,
    "sampler_bottom_left": BUTTON_SAMPLER_BOTTOM_LEFT,
    "sampler_bottom_right": BUTTON_SAMPLER_BOTTOM_RIGHT,
    "sampler_clear": BUTTON_SAMPLER_CLEAR,
    "sampler_select_a": BUTTON_SAMPLER_SELECT_A,
    "sampler_select_b": BUTTON_SAMPLER_SELECT_B,
    "sampler_select_c": BUTTON_SAMPLER_SELECT_C,
    "sampler_top_left": BUTTON_SAMPLER_TOP_LEFT,
    "sampler_top_right": BUTTON_SAMPLER_TOP_RIGHT,
}

NAME_MAP: Final[dict[str, MapItem]] = {
    "a": MapItem(key="A", name="Fader 1", icon="mdi:tune-vertical-variant"),
    "A": MapItem(key="A", name="Fader 1", icon="mdi:tune-vertical-variant"),
    "b": MapItem(key="B", name="Fader 2", icon="mdi:tune-vertical-variant"),
    "B": MapItem(key="B", name="Fader 2", icon="mdi:tune-vertical-variant"),
    "bleep": MapItem(key="Bleep", name=BUTTON_BLEEP, icon="mdi:exclamation"),
    "c": MapItem(key="C", name="Fader 3", icon="mdi:tune-vertical-variant"),
    "C": MapItem(key="C", name="Fader 3", icon="mdi:tune-vertical-variant"),
    "chat": MapItem(key="Chat", name="Chat", icon="mdi:chat"),
    "console": MapItem(key="Console", name="Console", icon="mdi:gamepad-variant"),
    "cough": MapItem(key="Cough", name=BUTTON_COUGH, icon="mdi:microphone-off"),
    "d": MapItem(key="D", name="Fader 4", icon="mdi:tune-vertical-variant"),
    "D": MapItem(key="D", name="Fader 4", icon="mdi:tune-vertical-variant"),
    "effect_fx": MapItem(
        key="effect_fx", name="Effect FX", icon="mdi:equalizer-outline"
    ),
    "effect_hard_tune": MapItem(
        key="effect_hard_tune", name="Effect Hard Tune", icon="mdi:knob"
    ),
    "effect_megaphone": MapItem(
        key="effect_megaphone", name="Effect Megaphone", icon="mdi:bullhorn-outline"
    ),
    "effect_robot": MapItem(
        key="effect_robot", name="Effect Robot", icon="mdi:robot-outline"
    ),
    "effect_select_1": MapItem(
        key="effect_select_1", name="Effect Select 1", icon="mdi:sawtooth-wave"
    ),
    "effect_select_2": MapItem(
        key="effect_select_2", name="Effect Select 2", icon="mdi:sawtooth-wave"
    ),
    "effect_select_3": MapItem(
        key="effect_select_3", name="Effect Select 3", icon="mdi:sawtooth-wave"
    ),
    "effect_select_4": MapItem(
        key="effect_select_4", name="Effect Select 4", icon="mdi:sawtooth-wave"
    ),
    "effect_select_5": MapItem(
        key="effect_select_5", name="Effect Select 5", icon="mdi:sawtooth-wave"
    ),
    "effect_select_6": MapItem(
        key="effect_select_6", name="Effect Select 6", icon="mdi:sawtooth-wave"
    ),
    "effect_select1": MapItem(
        key="effect_select1", name="Effect Select 1", icon="mdi:sawtooth-wave"
    ),
    "effect_select2": MapItem(
        key="effect_select2", name="Effect Select 2", icon="mdi:sawtooth-wave"
    ),
    "effect_select3": MapItem(
        key="effect_select3", name="Effect Select 3", icon="mdi:sawtooth-wave"
    ),
    "effect_select4": MapItem(
        key="effect_select4", name="Effect Select 4", icon="mdi:sawtooth-wave"
    ),
    "effect_select5": MapItem(
        key="effect_select5", name="Effect Select 5", icon="mdi:sawtooth-wave"
    ),
    "effect_select6": MapItem(
        key="effect_select6", name="Effect Select 6", icon="mdi:sawtooth-wave"
    ),
    "fader_1_mute": MapItem(
        key="fader_1_mute", name="Fader 1 Mute", icon="mdi:microphone-off"
    ),
    "fader_1": MapItem(key="fader_1", name="Fader 1", icon="mdi:volume-high"),
    "fader_2_mute": MapItem(
        key="fader_2_mute", name="Fader 2 Mute", icon="mdi:microphone-off"
    ),
    "fader_2": MapItem(key="fader_2", name="Fader 2", icon="mdi:volume-high"),
    "fader_3_mute": MapItem(
        key="fader_3_mute", name="Fader 3 Mute", icon="mdi:microphone-off"
    ),
    "fader_3": MapItem(key="fader_3", name="Fader 3", icon="mdi:volume-high"),
    "fader_4_mute": MapItem(
        key="fader_4_mute", name="Fader 4 Mute", icon="mdi:microphone-off"
    ),
    "fader_4": MapItem(key="fader_4", name="Fader 4", icon="mdi:volume-high"),
    "fader1_mute": MapItem(
        key="fader1_mute", name="Fader 1 Mute", icon="mdi:microphone-off"
    ),
    "fader2_mute": MapItem(
        key="fader2_mute", name="Fader 2 Mute", icon="mdi:microphone-off"
    ),
    "fader3_mute": MapItem(
        key="fader3_mute", name="Fader 3 Mute", icon="mdi:microphone-off"
    ),
    "fader4_mute": MapItem(
        key="fader4_mute", name="Fader 4 Mute", icon="mdi:microphone-off"
    ),
    "headphones": MapItem(key="Headphones", name="Headphones", icon="mdi:headphones"),
    "line_in": MapItem(
        key="LineIn", name="Line In", icon="mdi:audio-input-stereo-minijack"
    ),
    "line_out": MapItem(
        key="LineOut", name="Line Out", icon="mdi:audio-input-stereo-minijack"
    ),
    "LineIn": MapItem(
        key="LineIn", name="Line In", icon="mdi:audio-input-stereo-minijack"
    ),
    "LineOut": MapItem(
        key="LineOut", name="Line Out", icon="mdi:audio-input-stereo-minijack"
    ),
    "mic_monitor": MapItem(
        key="MicMonitor", name="Microphone Monitor", icon="mdi:microphone-outline"
    ),
    "mic": MapItem(key="Mic", name="Microphone", icon="mdi:microphone"),
    "Mic": MapItem(key="Mic", name="Microphone", icon="mdi:microphone"),
    "MicMonitor": MapItem(
        key="MicMonitor", name="Microphone Monitor", icon="mdi:microphone-outline"
    ),
    "music": MapItem(key="Music", name="Music", icon="mdi:music"),
    "Music": MapItem(key="Music", name="Music", icon="mdi:music"),
    "mute_all": MapItem(key="mute_all", name="Mute All", icon="mdi:microphone-off"),
    "mute_chat": MapItem(key="mute_chat", name="Mute Chat", icon="mdi:microphone-off"),
    "mute_console": MapItem(
        key="mute_console", name="Mute Console", icon="mdi:microphone-off"
    ),
    "mute_line_in": MapItem(
        key="mute_line_in", name="Mute Line In", icon="mdi:microphone-off"
    ),
    "mute_line_out": MapItem(
        key="mute_line_out", name="Mute Line Out", icon="mdi:microphone-off"
    ),
    "mute_mic": MapItem(
        key="mute_mic", name="Mute Microphone", icon="mdi:microphone-off"
    ),
    "mute_microphone": MapItem(
        key="mute_microphone", name="Mute Microphone", icon="mdi:microphone-off"
    ),
    "mute_music": MapItem(
        key="mute_music", name="Mute Music", icon="mdi:microphone-off"
    ),
    "mute_system": MapItem(
        key="mute_system", name="Mute System", icon="mdi:microphone-off"
    ),
    "mute": MapItem(key="Mute", name="Mute", icon="mdi:microphone-off"),
    "sample": MapItem(key="Sample", name="Sample", icon="mdi:music-note"),
    "sampler_bottom_left": MapItem(
        key="sampler_bottom_left", name="Sampler Bottom Left", icon="mdi:music-note"
    ),
    "sampler_bottom_right": MapItem(
        key="sampler_bottom_right", name="Sampler Bottom Right", icon="mdi:music-note"
    ),
    "sampler_clear": MapItem(
        key="sampler_clear", name="Sampler Clear", icon="mdi:music-note"
    ),
    "sampler_select_a": MapItem(
        key="sampler_select_a", name="Sampler Select A", icon="mdi:music-note"
    ),
    "sampler_select_b": MapItem(
        key="sampler_select_b", name="Sampler Select B", icon="mdi:music-note"
    ),
    "sampler_select_c": MapItem(
        key="sampler_select_c", name="Sampler Select C", icon="mdi:music-note"
    ),
    "sampler_top_left": MapItem(
        key="sampler_top_left", name="Sampler Top Left", icon="mdi:music-note"
    ),
    "sampler_top_right": MapItem(
        key="sampler_top_right", name="Sampler Top Right", icon="mdi:music-note"
    ),
    "system": MapItem(key="System", name="System", icon="mdi:music-box-outline"),
    "System": MapItem(key="System", name="System", icon="mdi:music-box-outline"),
}
