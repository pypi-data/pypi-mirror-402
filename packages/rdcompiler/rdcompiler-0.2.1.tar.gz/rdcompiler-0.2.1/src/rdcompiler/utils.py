import random

GENERATE_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def dict_get_random_name(mapping: dict, orig_name: str, length: int, chars=GENERATE_CHARS) -> str:
    if orig_name in mapping:
        return mapping[orig_name]

    name = ''.join(random.choices(chars, k=length))
    while name in mapping.values():
        name = ''.join(random.choices(chars, k=length))

    mapping[orig_name] = name
    return name


def beats_per_bar_list(events: list[dict]) -> list[int]:
    beats = [8]
    set_beats = [False]
    for event in events:
        beats.extend(beats[-1] for _ in range(event['bar'] - len(beats) + 1))
        set_beats.extend(set_beats[-1] for _ in range(event['bar'] - len(set_beats) + 1))

        if event['type'] != 'SetCrotchetsPerBar':
            continue

        bar = event['bar']
        beats_per_bar = event['crotchetsPerBar']
        set_beats[bar] = True
        beats[bar] = beats_per_bar
        bar += 1

        while len(beats) - 1 >= bar and not set_beats[bar]:
            beats[bar] = beats_per_bar
            bar += 1

    return beats


def find_event_position(beats: list[int], offset: float) -> tuple[int, float]:
    beat = 1
    for beats_per_bar in beats[1:]:
        if offset < beats_per_bar:
            return beat, offset + 1

        offset -= beats_per_bar
        beat += 1

    while True:
        if offset < beats[-1]:
            return beat, offset + 1

        offset -= beats[-1]
        beat += 1


def find_event_offset(beats: list[int], bar: int, beat: float) -> float:
    return sum(beats[1:bar]) + beat - 1
