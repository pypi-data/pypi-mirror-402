class WASDMaps:
    KEY_TO_DIRECTION_MAP = {
        "W": "forward",
        "A": "left",
        "S": "backward",
        "D": "right",
        "SPACE": "up",
        "X": "down",
    }


class MovementMaps:
    DIRECTION_TO_MOVEMENT_MAP = {
        "forward": "+forward",
        "left": "+left",
        "backward": "+backward",
        "right": "+right",
        "up": "+up",
        "down": "+down",
    }

    OPPOSITE_DIRECTION = {
        "forward": "backward",
        "backward": "forward",
        "left": "right",
        "right": "left",
        "up": "up",
        "down": "down",
    }


class ChangelingMaps:
    WS_FORMS = {
        "bolt": "dark nova",
        "blast": "dark nova",
        "detonation": "dark nova",
        "emanation": "dark nova",
        "strike": "black dwarf",
        "smite": "black dwarf",
        "antagonize": "black dwarf",
        "mire": "black dwarf",
        "drain": "black dwarf",
    }

    PB_FORMS = {
        "bolt": "bright nova",
        "blast": "bright nova",
        "detonation": "bright nova",
        "scatter": "bright nova",
        "strike": "white dwarf",
        "smite": "white dwarf",
        "antagonize": "white dwarf",
        "flare": "white dwarf",
        "sublimation": "white dwarf",
    }
