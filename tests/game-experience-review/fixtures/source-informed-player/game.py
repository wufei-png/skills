"""Authored synthetic implementation; no renderer, input device, or human session."""

from dataclasses import dataclass


@dataclass
class State:
    minutes: int = 0
    investigation_open: bool = True
    transport_committed: bool = False


def visible_actions(state: State) -> list[tuple[str, int]]:
    if state.transport_committed:
        return []
    actions = [("Start official evacuation", 6)]
    if state.investigation_open:
        actions.insert(0, ("Inspect floor 9", 3))
    return actions


def start_evacuation(state: State) -> str:
    state.minutes += 6
    state.transport_committed = True
    state.investigation_open = False
    return "Transport committed. Further floor inspections are unavailable."


def hidden_roof_access(code: str) -> bool:
    return code == "ORCHID-72"
