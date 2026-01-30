#!/usr/bin/env python3
"""
Test script for Olbrain Python SDK
Tests agent eQG36P3MaS3T6craxbET with real-time streaming
"""

import sys
import os
import logging
import time
import threading

# Add current directory to path to use local SDK
sys.path.insert(0, os.path.dirname(__file__))

from olbrain import AgentClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main test function"""

    # Agent configuration
    AGENT_ID = "eQG36P3MaS3T6craxbET"

    print("\n" + "=" * 70)
    print("🧪 OLBRAIN SDK TEST")
    print("=" * 70)
    print(f"\n🎯 Target Agent: {AGENT_ID}")

    # Get API key
    API_KEY = "ak_07d092742bc1ece0ad2cf4981d3a43f3e26bc12f23667610e72d33dbdf8b40ba"

    print("\n" + "=" * 70)
    print("🚀 STARTING TEST")
    print("=" * 70)

    # Message handler with nice formatting
    def on_message(msg):
        """Handle incoming messages"""
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        tokens = msg.get('token_usage', {})
        total_tokens = tokens.get('total', 0)
        cost = tokens.get('cost', 0)

        # Format output
        if role == 'user':
            emoji = "👤"
            color_code = "\033[94m"  # Blue
        else:
            emoji = "🤖"
            color_code = "\033[92m"  # Green

        reset_code = "\033[0m"

        print(f"\n{color_code}{emoji} [{role.upper()}]{reset_code}")
        print(f"   {content}")

        if total_tokens > 0:
            print(f"   💰 Tokens: {total_tokens} | Cost: ${cost:.6f}")

    # Create client
    try:
        print("\n📦 Initializing SDK client...")
        client = AgentClient(agent_id=AGENT_ID, api_key=API_KEY)
        print(f"✅ Client initialized: {client}")

    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
        return 1

    try:
        # Create session
        print("\n📝 Creating session...")
        session = client.create_session(on_message=on_message)
        print(f"✅ Session created: {session}")
        print("   📡 Real-time message stream active")

        print("\n" + "=" * 70)
        print("💬 INTERACTIVE MODE")
        print("=" * 70)
        print("\n   ✨ Type your messages below")
        print("   📨 All responses will appear in real-time")
        print("   ⏰ Scheduled messages will arrive automatically")
        print("   🚪 Type 'exit' or 'quit' to stop")
        print("   ⏹️  Press Ctrl+C to force exit\n")

        # Main thread handles input (SSE stream runs in background)
        while True:
            try:
                print("USER > ", end="", flush=True)
                user_input = input()

                if user_input.strip().lower() in ['exit', 'quit']:
                    print("\n👋 Exiting...")
                    break

                if user_input.strip():
                    client.send(session, user_input)

            except EOFError:
                # Ctrl+D pressed
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"\n⚠️  Error: {e}")
                break

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("👋 GRACEFUL SHUTDOWN")
        print("=" * 70)
        print("\n✅ Test completed successfully!")

    except Exception as e:
        print("\n\n" + "=" * 70)
        print("❌ ERROR OCCURRED")
        print("=" * 70)
        print(f"\n💥 Error: {e}")
        print("\n📋 Traceback:")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        print("\n🧹 Cleaning up...")
        client.close()
        print("✅ Cleanup complete")
        print("\n" + "=" * 70)
        print("🏁 TEST FINISHED")
        print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
