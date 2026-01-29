from unittest.mock import MagicMock
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents.middleware import ModelRequest
from langchain_middleware_notepad.middleware import NotePadMiddleware

def test_middleware_tools_registration():
    mw = NotePadMiddleware()
    tools = mw.tools
    assert len(tools) == 4
    tool_names = {t.name for t in tools}
    expected = {
        "notepad_append",
        "notepad_replace",
        "notepad_read",
        "notepad_clear",
    }
    assert tool_names == expected

def test_middleware_prompt_injection():
    mw = NotePadMiddleware()
    
    # Mock request
    initial_sys_msg = SystemMessage(content="You are a helper.")
    request = ModelRequest(
        messages=[HumanMessage(content="Hi")],
        state={},
        runtime=MagicMock(),
        tools=[],
        tool_choice=None,
        system_message=initial_sys_msg,
        model="mock_model"
    )
    
    # Mock handler (pass-through)
    def mock_handler(req):
        return req
        
    # Execute hook
    modified_request = mw.wrap_model_call(request, mock_handler)
    
    # Verify SystemMessage updated
    assert isinstance(modified_request.system_message, SystemMessage)
    content = modified_request.system_message.content
    assert "You are a helper." in content
    assert "NOTEPAD ACCESS" in content

def test_middleware_missing_system_message():
    mw = NotePadMiddleware()
    
    request = ModelRequest(
        messages=[HumanMessage(content="Hi")],
        state={},
        runtime=MagicMock(),
        tools=[],
        tool_choice=None,
        system_message=None,  # Missing system message
        model="mock_model"
    )
    
    def mock_handler(req):
        return req
        
    modified_request = mw.wrap_model_call(request, mock_handler)
    assert isinstance(modified_request.system_message, SystemMessage)
    assert "NOTEPAD ACCESS" in modified_request.system_message.content
