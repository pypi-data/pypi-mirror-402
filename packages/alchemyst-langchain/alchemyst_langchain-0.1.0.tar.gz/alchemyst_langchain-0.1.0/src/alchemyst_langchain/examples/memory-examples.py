import os
import uuid

from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

from alchemyst_langchain.memory import AlchemystMemory

# Load environment variables
load_dotenv()


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def example_1_basic_usage():
    """
    Basic conversation showing how AlchemystMemory remembers context.

    Key Learning: Memory persists within a session.
    """
    print_section("Example 1: Basic Persistent Memory")

    # Create unique session
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}\n")

    # Initialize memory and chain
    memory = AlchemystMemory(
        api_key=os.getenv("ALCHEMYST_AI_API_KEY"), session_id=session_id
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = ConversationChain(llm=llm, memory=memory)

    # Conversation that builds context
    print("User: Hi, my name is Alice and I'm from New York.")
    response = chain.invoke({"input": "Hi, my name is Alice and I'm from New York."})
    print(f"Bot: {response['response']}\n")

    print("User: What's my name?")
    response = chain.invoke({"input": "What's my name?"})
    print(f"Bot: {response['response']}\n")

    print("User: Where am I from?")
    response = chain.invoke({"input": "Where am I from?"})
    print(f"Bot: {response['response']}")

    print("\n✅ Memory persists! The bot remembers your name and location.")


def example_2_multi_user():
    """
    Demonstrate how different users have isolated memory.

    Key Learning: Each session_id creates an isolated memory space.
    """
    print_section("Example 2: Multi-User Isolated Memory")

    # Create sessions for two users
    alice_session = "user_alice"
    bob_session = "user_bob"

    print("Setting up Alice and Bob with separate sessions...\n")

    # Alice's conversation
    print("--- Alice's Conversation ---")
    alice_memory = AlchemystMemory(
        api_key=os.getenv("ALCHEMYST_AI_API_KEY"), session_id=alice_session
    )
    alice_chain = ConversationChain(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0), memory=alice_memory
    )

    print("Alice: My favorite color is blue.")
    response = alice_chain.invoke({"input": "My favorite color is blue."})
    print(f"Bot: {response['response']}\n")

    # Bob's conversation
    print("--- Bob's Conversation ---")
    bob_memory = AlchemystMemory(
        api_key=os.getenv("ALCHEMYST_AI_API_KEY"), session_id=bob_session
    )
    bob_chain = ConversationChain(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0), memory=bob_memory
    )

    print("Bob: My favorite color is red.")
    response = bob_chain.invoke({"input": "My favorite color is red."})
    print(f"Bot: {response['response']}\n")

    # Verify isolation
    print("--- Verify Each User Has Separate Memory ---")
    print("Alice: What's my favorite color?")
    response = alice_chain.invoke({"input": "What's my favorite color?"})
    print(f"Bot to Alice: {response['response']}\n")

    print("Bob: What's my favorite color?")
    response = bob_chain.invoke({"input": "What's my favorite color?"})
    print(f"Bot to Bob: {response['response']}")

    print("\n✅ Each user has completely isolated memory!")


def example_3_session_continuation():
    """
    Show how conversations can continue later with the same session.

    Key Learning: Use the same session_id to continue previous conversations.
    """
    print_section("Example 3: Continuing Conversations Later")

    # Use a consistent session ID (in production, store this in your database)
    session_id = "customer_12345"

    print(f"Customer Session ID: {session_id}")
    print("(In production, you'd retrieve this from your database)\n")

    memory = AlchemystMemory(
        api_key=os.getenv("ALCHEMYST_AI_API_KEY"), session_id=session_id
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = ConversationChain(llm=llm, memory=memory)

    # First interaction (e.g., Day 1)
    print("--- First Contact (Day 1) ---")
    print("Customer: I'm having an issue with order #5678.")
    response = chain.invoke({"input": "I'm having an issue with order #5678."})
    print(f"Support: {response['response']}\n")

    # Later interaction (e.g., Day 2)
    print("--- Follow-up (Day 2) ---")
    print("Customer: I'm calling back about my order issue from yesterday.")
    response = chain.invoke(
        {"input": "I'm calling back about my order issue from yesterday."}
    )
    print(f"Support: {response['response']}")

    print("\n✅ The bot remembers the previous conversation!")
    print("💡 Tip: Store session_id in your database linked to user/customer ID")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  ALCHEMYST MEMORY - ESSENTIAL EXAMPLES")
    print("=" * 70)

    # Check for required API keys
    if not os.getenv("ALCHEMYST_AI_API_KEY"):
        print("\n❌ ERROR: ALCHEMYST_AI_API_KEY not found!")
        print("Please set it in your .env file:")
        print("  ALCHEMYST_API_KEY=your_key_here\n")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found!")
        print("Please set it in your .env file:")
        print("  OPENAI_API_KEY=your_key_here\n")
        return

    print("\n✅ API keys found. Running examples...\n")

    try:
        # Run all examples
        example_1_basic_usage()
        input("\nPress Enter to continue to Example 2...")

        example_2_multi_user()
        input("\nPress Enter to continue to Example 3...")

        example_3_session_continuation()
        input("\nPress Enter to continue to Example 4...")

    except Exception as e:
        print(f"\n Error running examples: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API keys in .env file")
        print("2. Ensure you have internet connection")
        print("3. Verify API keys are valid")


if __name__ == "__main__":
    main()
