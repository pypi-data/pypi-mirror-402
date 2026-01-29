from typing_extensions import TypedDict


class NotepadState(TypedDict):
    """
    Extends the agent state with a plain-text notepad.
    """
    notepad: str
