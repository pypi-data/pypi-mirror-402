# Examples

This directory contains example scripts demonstrating the usage of `langchain-notepad-middleware`.

## demo.py

A standalone script that runs an agent with the Notepad Middleware. It runs a story generation loop to demonstrate the `notepad_append` and `notepad_read` tools in action over multiple turns.

### Prerequisites

1.  **Install the package**:
    ```bash
    pip install -e ..
    ```

2.  **Ollama Setup**:
    -   You need [Ollama](https://ollama.com/) installed and running.
    -   Pull a model, for example `llama3` or `nemotron-3-nano`:
        ```bash
        ollama pull llama3
        ```
    -   **Model Selection**: Update the `model=` argument in `demo.py` to match the model you have installed.
        -   [Ollama Model Library](https://ollama.com/library)

3.  **LangSmith Tracing (Optional but Recommended)**:
    -   LangSmith helps you trace and debug the agent's internal steps (tool calls, state updates).
    -   [LangSmith Setup Guide](https://docs.smith.langchain.com/)
    -   Set your environment variables:
        ```bash
        export LANGCHAIN_TRACING_V2=true
        export LANGCHAIN_API_KEY=<your-api-key>
        ```
    -   The script sets `LANGSMITH_TRACING="true"` internally, but you need the API key in your environment.

### Running the Demo

```bash
python demo.py
```
