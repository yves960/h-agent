"""
h_agent/buddy/sprites.py - ASCII Art Sprites

Each sprite is 5 lines tall. Multiple frames per species for idle fidget animation.
Line 0 is the hat slot - must be blank in frames 0-1.
"""

from h_agent.buddy.types import Species, Hat

# Each sprite is 5 lines tall, 12 wide (after {E}→1char substitution).
# Multiple frames per species for idle fidget animation.
# Line 0 is the hat slot — must be blank in frames 0-1; frame 2 may use it.
BODIES: dict[Species, list[list[str]]] = {
    Species.DUCK: [
        [
            "            ",
            "    __      ",
            "  <({E} )___  ",
            "   (  ._>   ",
            "    `--´    ",
        ],
        [
            "            ",
            "    __      ",
            "  <({E} )___  ",
            "   (  ._>   ",
            "    `--´~   ",
        ],
        [
            "            ",
            "    __      ",
            "  <({E} )___  ",
            "   (  .__>  ",
            "    `--´    ",
        ],
    ],
    Species.GOOSE: [
        [
            "            ",
            "     ({E}>    ",
            "     ||     ",
            "   _(__)_   ",
            "    ^^^^    ",
        ],
        [
            "            ",
            "    ({E}>     ",
            "     ||     ",
            "   _(__)_   ",
            "    ^^^^    ",
        ],
        [
            "            ",
            "     ({E}>>   ",
            "     ||     ",
            "   _(__)_   ",
            "    ^^^^    ",
        ],
    ],
    Species.BLOB: [
        [
            "            ",
            "   .----.   ",
            "  ( {E}  {E} )  ",
            "  (      )  ",
            "   `----´   ",
        ],
        [
            "            ",
            "  .------.  ",
            " (  {E}  {E}  ) ",
            " (        ) ",
            "  `------´  ",
        ],
        [
            "            ",
            "    .--.    ",
            "   ({E}  {E})   ",
            "   (    )   ",
            "    `--´    ",
        ],
    ],
    Species.CAT: [
        [
            "            ",
            "   /\\_/\\    ",
            "  ( {E}   {E})  ",
            "  (  ω  )   ",
            "  (\")_(\")   ",
        ],
        [
            "            ",
            "   /\\_/\\    ",
            "  ( {E}   {E})  ",
            "  (  ω  )   ",
            "  (\")_(\")~  ",
        ],
        [
            "            ",
            "   /\\-/\\    ",
            "  ( {E}   {E})  ",
            "  (  ω  )   ",
            "  (\")_(\")   ",
        ],
    ],
    Species.DRAGON: [
        [
            "            ",
            "  /^\\  /^\\  ",
            " <  {E}  {E}  > ",
            " (   ~~   ) ",
            "  `-vvvv-´  ",
        ],
        [
            "            ",
            "  /^\\  /^\\  ",
            " <  {E}  {E}  > ",
            " (        ) ",
            "  `-vvvv-´  ",
        ],
        [
            "   ~    ~   ",
            "  /^\\  /^\\  ",
            " <  {E}  {E}  > ",
            " (   ~~   ) ",
            "  `-vvvv-´  ",
        ],
    ],
    Species.OCTOPUS: [
        [
            "            ",
            "   .----.   ",
            "  ( {E}  {E} )  ",
            "  (______)  ",
            "  /\\/\\/\\/\\  ",
        ],
        [
            "            ",
            "   .----.   ",
            "  ( {E}  {E} )  ",
            "  (______)  ",
            "  \\/\\/\\/\\/  ",
        ],
        [
            "     o      ",
            "   .----.   ",
            "  ( {E}  {E} )  ",
            "  (______)  ",
            "  /\\/\\/\\/\\  ",
        ],
    ],
    Species.OWL: [
        [
            "            ",
            "   /\\  /\\   ",
            "  (({E})({E}))  ",
            "  (  ><  )  ",
            "   `----´   ",
        ],
        [
            "            ",
            "   /\\  /\\   ",
            "  (({E})({E}))  ",
            "  (  ><  )  ",
            "   .----.   ",
        ],
        [
            "            ",
            "   /\\  /\\   ",
            "  (({E})(-))  ",
            "  (  ><  )  ",
            "   `----´   ",
        ],
    ],
    Species.PENGUIN: [
        [
            "            ",
            "  .---.     ",
            "  ({E}>{E})     ",
            " /(   )\\    ",
            "  `---´     ",
        ],
        [
            "            ",
            "  .---.     ",
            "  ({E}>{E})     ",
            " |(   )|    ",
            "  `---´     ",
        ],
        [
            "  .---.     ",
            "  ({E}>{E})     ",
            " /(   )\\    ",
            "  `---´     ",
            "   ~ ~      ",
        ],
    ],
    Species.TURTLE: [
        [
            "            ",
            "   _,--._   ",
            "  ( {E}  {E} )  ",
            " /[______]\\ ",
            "  ``    ``  ",
        ],
        [
            "            ",
            "   _,--._   ",
            "  ( {E}  {E} )  ",
            " /[______]\\ ",
            "   ``  ``   ",
        ],
        [
            "            ",
            "   _,--._   ",
            "  ( {E}  {E} )  ",
            " /[======]\\ ",
            "  ``    ``  ",
        ],
    ],
    Species.SNAIL: [
        [
            "            ",
            " {E}    .--.  ",
            "  \\  ( @ )  ",
            "   \\_`--´   ",
            "  ~~~~~~~   ",
        ],
        [
            "            ",
            "  {E}   .--.  ",
            "  |  ( @ )  ",
            "   \\_`--´   ",
            "  ~~~~~~~   ",
        ],
        [
            "            ",
            " {E}    .--.  ",
            "  \\  ( @  ) ",
            "   \\_`--´   ",
            "   ~~~~~~   ",
        ],
    ],
    Species.GHOST: [
        [
            "            ",
            "   .----.   ",
            "  / {E}  {E} \\  ",
            "  |      |  ",
            "  ~`~``~`~  ",
        ],
        [
            "            ",
            "   .----.   ",
            "  / {E}  {E} \\  ",
            "  |      |  ",
            "  `~`~~`~`  ",
        ],
        [
            "    ~  ~    ",
            "   .----.   ",
            "  / {E}  {E} \\  ",
            "  |      |  ",
            "  ~~`~~`~~  ",
        ],
    ],
    Species.AXOLOTL: [
        [
            "            ",
            "}~(______)~{",
            "}~({E} .. {E})~{",
            "  ( .--. )  ",
            "  (_/  \\_)  ",
        ],
        [
            "            ",
            "~}(______){~",
            "~}({E} .. {E}){~",
            "  ( .--. )  ",
            "  (_/  \\_)  ",
        ],
        [
            "            ",
            "}~(______)~{",
            "}~({E} .. {E})~{",
            "  (  --  )  ",
            "  ~_/  \\_~  ",
        ],
    ],
    Species.CAPYBARA: [
        [
            "            ",
            "  n______n  ",
            " ( {E}    {E} ) ",
            " (   oo   ) ",
            "  `------´  ",
        ],
        [
            "            ",
            "  n______n  ",
            " ( {E}    {E} ) ",
            " (   Oo   ) ",
            "  `------´  ",
        ],
        [
            "    ~  ~    ",
            "  u______n  ",
            " ( {E}    {E} ) ",
            " (   oo   ) ",
            "  `------´  ",
        ],
    ],
    Species.CACTUS: [
        [
            "            ",
            " n  ____  n ",
            " | |{E}  {E}| | ",
            " |_|    |_| ",
            "   |    |   ",
        ],
        [
            "            ",
            "    ____    ",
            " n |{E}  {E}| n ",
            " |_|    |_| ",
            "   |    |   ",
        ],
        [
            " n        n ",
            " |  ____  | ",
            " | |{E}  {E}| | ",
            " |_|    |_| ",
            "   |    |   ",
        ],
    ],
    Species.ROBOT: [
        [
            "            ",
            "   .[||].   ",
            "  [ {E}  {E} ]  ",
            "  [ ==== ]  ",
            "  `------´  ",
        ],
        [
            "            ",
            "   .[||].   ",
            "  [ {E}  {E} ]  ",
            "  [ -==- ]  ",
            "  `------´  ",
        ],
        [
            "     *      ",
            "   .[||].   ",
            "  [ {E}  {E} ]  ",
            "  [ ==== ]  ",
            "  `------´  ",
        ],
    ],
    Species.RABBIT: [
        [
            "            ",
            "   (\\__/)   ",
            "  ( {E}  {E} )  ",
            " =(  ..  )= ",
            "  (\")__(\")  ",
        ],
        [
            "            ",
            "   (|__/)   ",
            "  ( {E}  {E} )  ",
            " =(  ..  )= ",
            "  (\")__(\")  ",
        ],
        [
            "            ",
            "   (\\__/)   ",
            "  ( {E}  {E} )  ",
            " =( .  . )= ",
            "  (\")__(\")  ",
        ],
    ],
    Species.MUSHROOM: [
        [
            "            ",
            " .-oOO-o-. ",
            "(__________)",
            "   |{E}  {E}|   ",
            "   |____|   ",
        ],
        [
            "            ",
            " .-O-oo-O-. ",
            "(__________)",
            "   |{E}  {E}|   ",
            "   |____|   ",
        ],
        [
            "   . o  .   ",
            " .-oOO-o-. ",
            "(__________)",
            "   |{E}  {E}|   ",
            "   |____|   ",
        ],
    ],
    Species.CHONK: [
        [
            "            ",
            "  /\\    /\\  ",
            " ( {E}    {E} ) ",
            " (   ..   ) ",
            "  `------´  ",
        ],
        [
            "            ",
            "  /\\    /|  ",
            " ( {E}    {E} ) ",
            " (   ..   ) ",
            "  `------´  ",
        ],
        [
            "            ",
            "  /\\    /\\  ",
            " ( {E}    {E} ) ",
            " (   ..   ) ",
            "  `------´~ ",
        ],
    ],
}

HAT_LINES: dict[Hat, str] = {
    Hat.NONE: "",
    Hat.CROWN: "   \\^^^/    ",
    Hat.TOPHAT: "   [___]    ",
    Hat.PROPELLER: "    -+-     ",
    Hat.HALO: "   (   )    ",
    Hat.WIZARD: "    /^\\     ",
    Hat.BEANIE: "   (___)    ",
    Hat.TINYDUCK: "    ,>      ",
}


def render_sprite(bones, frame: int = 0) -> list[str]:
    """Render sprite frames with eye substitution and hat overlay."""
    frames = BODIES.get(bones.species, BODIES[Species.BLOB])
    body = [line.replace("{E}", bones.eye) for line in frames[frame % len(frames)]]
    lines = list(body)
    
    # Only replace with hat if line 0 is empty
    if bones.hat != Hat.NONE and lines[0].strip() == "":
        lines[0] = HAT_LINES[bones.hat]
    
    # Drop blank hat slot if all frames have blank line 0
    if not lines[0].strip() and all(not f[0].strip() for f in frames):
        lines.pop(0)
    
    return lines


def sprite_frame_count(species: Species) -> int:
    """Get number of frames for a species."""
    return len(BODIES.get(species, BODIES[Species.BLOB]))


def render_face(bones) -> str:
    """Render just the face portion for speech bubbles."""
    eye = bones.eye
    species = bones.species
    
    if species == Species.DUCK or species == Species.GOOSE:
        return f"({eye}>"
    elif species == Species.BLOB:
        return f"({eye}{eye})"
    elif species == Species.CAT:
        return f"={eye}ω{eye}="
    elif species == Species.DRAGON:
        return f"<{eye}~{eye}>"
    elif species == Species.OCTOPUS:
        return f"~({eye}{eye})~"
    elif species == Species.OWL:
        return f"({eye})({eye})"
    elif species == Species.PENGUIN:
        return f"({eye}>)"
    elif species == Species.TURTLE:
        return f"[{eye}_{eye}]"
    elif species == Species.SNAIL:
        return f"{eye}(@)"
    elif species == Species.GHOST:
        return f"/{eye}{eye}\\"
    elif species == Species.AXOLOTL:
        return f"}}{eye}.{eye}{{"
    elif species == Species.CAPYBARA:
        return f"({eye}oo{eye})"
    elif species == Species.CACTUS:
        return f"|{eye}  {eye}|"
    elif species == Species.ROBOT:
        return f"[{eye}{eye}]"
    elif species == Species.RABBIT:
        return f"({eye}..{eye})"
    elif species == Species.MUSHROOM:
        return f"|{eye}  {eye}|"
    elif species == Species.CHONK:
        return f"({eye}.{eye})"
    
    return f"({eye})"
