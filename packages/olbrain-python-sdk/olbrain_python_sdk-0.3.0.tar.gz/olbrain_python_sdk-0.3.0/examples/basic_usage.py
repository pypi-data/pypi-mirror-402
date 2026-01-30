"""
Basic usage examples for the Olbrain Python SDK.

This example demonstrates the fundamental features of the SDK including:
- Client initialization
- Session creation
- Sending messages (synchronous)
- Using model overrides
- Error handling
"""

import os
from olbrain import AgentClient, ChatResponse
from olbrain.exceptions import (
    OlbrainError,
    AuthenticationError,
    NetworkError
)


def main():
    """Basic usage example."""

    # Get credentials from environment variables
    api_key = os.getenv("OLBRAIN_API_KEY", "sk_live_your-api-key-here")
    agent_id = os.getenv("OLBRAIN_AGENT_ID", "your-agent-id-here")
    # Optional: custom agent URL (auto-constructed from agent_id if not provided)
    agent_url = os.getenv("OLBRAIN_AGENT_URL")

    if api_key == "sk_live_your-api-key-here" or agent_id == "your-agent-id-here":
        print("Please set OLBRAIN_API_KEY and OLBRAIN_AGENT_ID environment variables")
        print()
        print("Example:")
        print("  export OLBRAIN_API_KEY=sk_live_your_key_here")
        print("  export OLBRAIN_AGENT_ID=your-agent-id")
        return

    try:
        # Initialize the client
        client = AgentClient(
            agent_id=agent_id,
            api_key=api_key,
            agent_url=agent_url  # Optional - uses default Cloud Run URL if not provided
        )
        print(f"Client initialized for agent {agent_id}")
        print(f"Agent URL: {client.agent_url}")

        # -----------------------------------------------------------------
        # Example 1: Creating a session and sending messages
        # -----------------------------------------------------------------
        print("\n--- Example 1: Create Session and Send Messages ---")

        # Create a session (first message without session_id creates the session)
        session_id = client.create_session(
            title="Basic Demo Chat",
            user_id="demo-user-123",
            mode="production"
        )
        print(f"Session created: {session_id}")

        # Send a message and get response
        response_data = client.send(session_id, "Hello! Can you introduce yourself?")

        # Parse response
        response = ChatResponse.from_dict(response_data, session_id)
        print(f"Agent: {response.text}")
        if response.token_usage:
            print(f"Tokens used: {response.token_usage.total_tokens}")
        if response.model:
            print(f"Model: {response.model}")
        if response.cost:
            print(f"Cost: ${response.cost:.6f}")

        # Send another message in the same session
        response_data2 = client.send(session_id, "What can you help me with?")
        response2 = ChatResponse.from_dict(response_data2, session_id)
        print(f"\nAgent: {response2.text}")

        # -----------------------------------------------------------------
        # Example 2: Using model override
        # -----------------------------------------------------------------
        print("\n--- Example 2: Model Override ---")

        # Send message with specific model
        response_data = client.send(
            session_id,
            "Explain quantum computing in one sentence",
            model="gpt-4o"  # Override default model
        )
        response = ChatResponse.from_dict(response_data, session_id)
        print(f"Response: {response.text}")
        print(f"Model used: {response.model}")

        # -----------------------------------------------------------------
        # Example 3: Using metadata
        # -----------------------------------------------------------------
        print("\n--- Example 3: Message with Metadata ---")

        response_data = client.send(
            session_id,
            "Tell me a joke",
            metadata={"category": "humor", "source": "example"}
        )
        response = ChatResponse.from_dict(response_data, session_id)
        print(f"Agent: {response.text}")

        # -----------------------------------------------------------------
        # Example 4: Multiple sessions
        # -----------------------------------------------------------------
        print("\n--- Example 4: Multiple Independent Sessions ---")

        # Create a second session
        session2_id = client.create_session(
            title="Second Chat",
            user_id="another-user"
        )
        print(f"Second session created: {session2_id}")

        # Send message to second session
        response_data = client.send(session2_id, "Hi! What's your favorite color?")
        response = ChatResponse.from_dict(response_data, session2_id)
        print(f"Agent (Session 2): {response.text}")

        # Sessions are independent
        response_data = client.send(
            session2_id,
            "Do you remember what I asked in my first session?"
        )
        response = ChatResponse.from_dict(response_data, session2_id)
        print(f"Agent (Session 2): {response.text}")

        print("\nNote: Sessions are independent - each maintains its own conversation context")

    except AuthenticationError:
        print("Authentication failed. Please check your API key.")
    except NetworkError as e:
        print(f"Network error: {e}")
    except OlbrainError as e:
        print(f"Olbrain error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("\nClient closed")


if __name__ == "__main__":
    main()
