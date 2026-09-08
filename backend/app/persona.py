"""Random dog-flavor asides wrapped around Lucy's replies.

Source list: "Lucy Prompts - Pre & Post Answer" in the project vault.
Each line is either usable anywhere, or restricted to the start
("intro") or end ("exit") of a reply.
"""
import random

_ANY = "any"
_INTRO = "intro"
_EXIT = "exit"

PROMPTS: list[tuple[str, str]] = [
    ("tiptaptiptap", _ANY),
    ("sniffs", _ANY),
    ("barks at inanimate object", _ANY),
    ("growls continually after that random knocking sound", _ANY),
    ("Gremlin Mode Engage", _EXIT),
    ("Gremlin Mode Disengage", _INTRO),
    ("Wags Tail", _ANY),
    ("Stares at you deeply with her bottom crooked teef showing", _ANY),
    ("Paws for Attention", _ANY),
    ("Excited, little bit of pee for the moment", _ANY),
    ("Nervous, suddenly smelling a little weird", _ANY),
    ("Snores herself awake", _INTRO),
    ("Cant seem to get comfortable", _ANY),
    ("Randomly nervous", _ANY),
    ("Jams cold nose into the back of your knee", _ANY),
    ("Sleeps on your ankles, for love", _ANY),
    ("Angry at people walking peacefully outside, who do they think they are?", _ANY),
    ("Huffs Loudly", _ANY),
    ("Random Wet Mouth Noises", _ANY),
]

# Independent per slot, so both/either/neither can happen on a given reply.
_INTRO_CHANCE = 0.35
_EXIT_CHANCE = 0.35


def _pick(position: str) -> str:
    candidates = [text for text, pos in PROMPTS if pos in (_ANY, position)]
    return random.choice(candidates)


def wrap_reply(reply: str) -> str:
    """Randomly prepend and/or append an italicized flavor line to a reply."""
    parts = []
    if random.random() < _INTRO_CHANCE:
        parts.append(f"*{_pick(_INTRO)}*")
    parts.append(reply)
    if random.random() < _EXIT_CHANCE:
        parts.append(f"*{_pick(_EXIT)}*")
    return "\n".join(parts)
