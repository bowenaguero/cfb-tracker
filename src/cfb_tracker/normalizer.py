import hashlib
import re
import unicodedata


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)  # remove punctuation except hyphens
    name = re.sub(r"\s+", " ", name)
    return name


POSITION_MAP = {
    "quarterback": "qb",
    "running back": "rb",
    "wide receiver": "wr",
    "tight end": "te",
    "offensive tackle": "ot",
    "offensive guard": "og",
    "offensive line": "ol",
    "center": "c",
    "defensive end": "de",
    "defensive tackle": "dt",
    "defensive line": "dl",
    "linebacker": "lb",
    "inside linebacker": "ilb",
    "outside linebacker": "olb",
    "cornerback": "cb",
    "safety": "s",
    "free safety": "fs",
    "strong safety": "ss",
    "athlete": "ath",
    "kicker": "k",
    "punter": "p",
    "long snapper": "ls",
    "edge": "edge",
}


def normalize_position(position: str) -> str:
    pos = position.lower().strip()
    return POSITION_MAP.get(pos, pos)


SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def get_name_key(name: str) -> str:
    normalized = normalize_name(name)
    parts = normalized.split()

    # Remove suffixes from end
    while parts and parts[-1] in SUFFIXES:
        parts.pop()

    if len(parts) < 2:
        return normalized

    first_letter = parts[0][0]

    # Get last name, take part after hyphen if hyphenated
    lastname = parts[-1]
    if "-" in lastname:
        lastname = lastname.split("-")[-1]

    return f"{first_letter}{lastname}"


def generate_id(name: str) -> str:
    return hashlib.sha256(get_name_key(name).encode()).hexdigest()[:16]
