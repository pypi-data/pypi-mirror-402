"""Core signals for Red9 event dispatching.

Uses blinker for decoupled, high-performance in-process messaging.
"""

from blinker import Signal

# UI Events (phase changes, tool calls, status updates)
# Sender: The component emitting the event (Task, Agent, Tool)
# Data: dict with 'type' and other fields
ui_event = Signal("ui_event")

# Token Streaming (LLM output)
# Sender: The provider or agent
# Data: str (the token)
token_stream = Signal("token_stream")
