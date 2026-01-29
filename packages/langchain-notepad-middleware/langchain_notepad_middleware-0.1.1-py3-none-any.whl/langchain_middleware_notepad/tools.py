from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.tools import tool, ToolRuntime


class NotepadAppendInput(BaseModel):
    """Input schema for appending text to the notepad."""
    text: str = Field(
        description="The text content to append to the existing notepad. This will be added on a new line."
    )


class NotepadReplaceInput(BaseModel):
    """Input schema for replacing the entire notepad content."""
    text: str = Field(
        description="The new text content that will completely replace the current notepad content."
    )


@tool(args_schema=NotepadAppendInput)
def notepad_append(
    text: str, 
    runtime: ToolRuntime
) -> Command:
    """
    Append text to the existing note in the notepad.
    
    Use this to add new information while preserving existing notes.
    The new text will be added on a new line after the current content.
    """
    current_note = runtime.state.get("notepad", "")
    if not current_note:
        new_note = text
    else:
        new_note = f"{current_note}\n{text}"
    
    return Command(
        update={
            "notepad": new_note,
            "messages": [ToolMessage(
                content="Appended text to notepad.", 
                tool_call_id=runtime.tool_call_id
            )]
        }
    )


@tool(args_schema=NotepadReplaceInput)
def notepad_replace(
    text: str, 
    runtime: ToolRuntime
) -> Command:
    """
    Replace the entire note in the notepad with new text.
    
    Use this to completely rewrite the notepad content, discarding all previous notes.
    This is useful for reorganizing or condensing information.
    """
    return Command(
        update={
            "notepad": text,
            "messages": [ToolMessage(
                content="Replaced notepad content.", 
                tool_call_id=runtime.tool_call_id
            )]
        }
    )


@tool
def notepad_read(runtime: ToolRuntime) -> str:
    """
    Read the full content of the notepad.
    
    Returns the current notepad content, or "<empty>" if the notepad is empty.
    Use this to review what information has been saved.
    """
    current_note = runtime.state.get("notepad", "")
    if not current_note:
        return "<empty>"
    return current_note


@tool
def notepad_clear(runtime: ToolRuntime) -> Command:
    """
    Clear the notepad, removing all content.
    
    Use this to start fresh or when the notepad information is no longer needed.
    This action cannot be undone.
    """
    return Command(
        update={
            "notepad": "",
            "messages": [ToolMessage(
                content="Cleared notepad.", 
                tool_call_id=runtime.tool_call_id
            )]
        }
    )
