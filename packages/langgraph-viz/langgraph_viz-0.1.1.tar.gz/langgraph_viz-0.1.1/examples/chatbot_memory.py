"""Example: Chatbot with conversational memory.

This example demonstrates:
- Persistent conversation memory using MemorySaver
- State tracking across multiple turns
- How conversation history accumulates in state
- Real-time visualization of evolving conversation state
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# Define conversation state
class ConversationState(TypedDict):
    """State for conversational chatbot."""
    messages: List[Dict[str, str]]  # List of {role, content} messages
    user_name: str  # Detected user name
    context: str  # Current conversation context
    turn_count: int  # Number of conversation turns


def process_input(state: ConversationState) -> ConversationState:
    """Process the user's latest message."""
    print(f"\n📥 Processing user input...")
    
    # Get the latest user message
    messages = state.get("messages", [])
    if not messages:
        return state
    
    latest_msg = messages[-1]["content"]
    print(f"   User said: {latest_msg}")
    
    # Simple name detection
    if "my name is" in latest_msg.lower():
        name = latest_msg.lower().split("my name is")[-1].strip().split()[0]
        state["user_name"] = name.title()
        print(f"   📝 Detected name: {state['user_name']}")
    
    # Update context based on keywords
    if any(word in latest_msg.lower() for word in ["weather", "forecast"]):
        state["context"] = "weather_inquiry"
    elif any(word in latest_msg.lower() for word in ["help", "support", "issue"]):
        state["context"] = "support_request"
    else:
        state["context"] = "general_chat"
    
    print(f"   📊 Context: {state['context']}")
    
    return state


def generate_response(state: ConversationState) -> ConversationState:
    """Generate an appropriate response based on state."""
    print(f"\n🤖 Generating response...")
    
    messages = state.get("messages", [])
    context = state.get("context", "general_chat")
    user_name = state.get("user_name", "")
    turn_count = state.get("turn_count", 0)
    
    # Craft response based on context and history
    greeting = f"Hi {user_name}! " if user_name else "Hello! "
    
    if context == "weather_inquiry":
        response = f"{greeting}The weather looks great today! ☀️ It's sunny with a high of 72°F."
    elif context == "support_request":
        response = f"{greeting}I'm here to help! What issue are you experiencing?"
    else:
        if turn_count == 0:
            response = "Hello! I'm a friendly chatbot. What's your name?"
        elif turn_count == 1 and user_name:
            response = f"Nice to meet you, {user_name}! How can I help you today?"
        else:
            response = f"{greeting}Is there anything else I can help you with?"
    
    # Add assistant message to history
    messages.append({"role": "assistant", "content": response})
    state["messages"] = messages
    
    print(f"   💬 Response: {response}")
    
    return state


def update_memory(state: ConversationState) -> ConversationState:
    """Update conversation metadata and memory."""
    print(f"\n💾 Updating conversation memory...")
    
    # Increment turn counter
    state["turn_count"] = state.get("turn_count", 0) + 1
    
    # Show memory stats
    msg_count = len(state.get("messages", []))
    print(f"   📈 Turn: {state['turn_count']}, Total messages: {msg_count}")
    print(f"   👤 User: {state.get('user_name', 'Unknown')}")
    print(f"   📌 Context: {state.get('context', 'none')}")
    
    return state


def create_chatbot():
    """Create the conversational chatbot workflow."""
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("process_input", process_input)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("update_memory", update_memory)
    
    # Define flow
    workflow.set_entry_point("process_input")
    workflow.add_edge("process_input", "generate_response")
    workflow.add_edge("generate_response", "update_memory")
    workflow.add_edge("update_memory", END)
    
    # Compile with memory checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 70)
    print("🤖 LangGraph Viz - Conversational Chatbot with Memory")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    # Create chatbot
    app = create_chatbot()
    
    print("\n🎨 Starting visualization server...")
    print("📊 Browser will open with live conversation visualization")
    print("💡 Watch how the conversation state evolves across turns!\n")
    
    # Start visualization
    with visualize(app, port=8765) as viz_app:
        # Simulate a multi-turn conversation
        conversation = [
            "Hello there!",
            "My name is Alice",
            "What's the weather like today?",
            "Thanks! That's helpful.",
        ]
        
        # Use a consistent thread_id to maintain conversation memory
        thread_id = "chat-demo-001"
        config = {"configurable": {"thread_id": thread_id}}
        
        for idx, user_msg in enumerate(conversation, 1):
            print(f"\n{'=' * 70}")
            print(f"Turn {idx}: User sends message")
            print('=' * 70)
            print(f"💬 User: {user_msg}\n")
            
            # Prepare input with user message
            input_state = {
                "messages": [{"role": "user", "content": user_msg}]
            }
            
            # Get current state if exists
            try:
                current_state = viz_app.get_state(config)
                if current_state and current_state.values:
                    # Append to existing messages
                    existing_messages = current_state.values.get("messages", [])
                    input_state["messages"] = existing_messages + input_state["messages"]
            except:
                pass  # First turn, no existing state
            
            # Stream execution
            for event in viz_app.stream(input_state, config):
                node_name = list(event.keys())[0]
                print(f"   ✓ Completed: {node_name}")
            
            print(f"\n   🎯 Turn {idx} complete - check visualization!")
            
            # Pause between conversation turns
            import time
            time.sleep(2)
        
        print(f"\n{'=' * 70}")
        print("✅ Conversation complete!")
        print("📊 View the full conversation history in the visualizer")
        print("💡 Notice how state accumulates with each turn")
        print('=' * 70)
        
        # Keep server running for inspection
        print("\n⏸️  Server running - Press Ctrl+C to exit\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
    
    print("\n✓ Visualization complete!\n")
