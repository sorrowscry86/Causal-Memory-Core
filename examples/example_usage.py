#!/usr/bin/env python3
"""
Example usage of the Causal Memory Core
Demonstrates how to use the memory system for recording and retrieving causal relationships
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from causal_memory_core import CausalMemoryCore

def main():
    """Demonstrate the Causal Memory Core functionality"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧠 Causal Memory Core - Example Usage")
    print("=" * 50)
    
    # Initialize the memory core
    print("\n1. Initializing Causal Memory Core...")
    try:
        memory = CausalMemoryCore()
        print("✅ Memory core initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing memory core: {e}")
        print("\nMake sure you have:")
        print("- Set OPENAI_API_KEY in your .env file")
        print("- Installed all dependencies: pip install -r requirements.txt")
        return
    
    print("\n2. Recording a sequence of events...")
    
    # Simulate a user workflow - file editing session
    events = [
        "The user opened the text editor application",
        "A blank document appeared on screen", 
        "The user typed 'Hello World' into the document",
        "The text appeared in the editor window",
        "The user pressed Ctrl+S to save",
        "A save dialog box opened",
        "The user entered 'hello.txt' as the filename",
        "The file was saved to disk",
        "The document title changed to show 'hello.txt'"
    ]
    
    for i, event in enumerate(events, 1):
        print(f"   📝 Adding event {i}: {event}")
        try:
            memory.add_event(event)
            print(f"   ✅ Event {i} recorded")
        except Exception as e:
            print(f"   ❌ Error recording event {i}: {e}")
    
    print(f"\n✅ Recorded {len(events)} events with automatic causal linking!")
    
    print("\n3. Querying the memory for causal context...")
    
    # Test different types of queries
    queries = [
        "How did the file get saved?",
        "What caused the text to appear?", 
        "Why did the document title change?",
        "What happened when the user pressed Ctrl+S?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n   🔍 Query {i}: {query}")
        try:
            context = memory.get_context(query)
            print(f"   📖 Context retrieved:")
            print(f"   {context}")
        except Exception as e:
            print(f"   ❌ Error retrieving context: {e}")
    
    print("\n4. Demonstrating semantic search capabilities...")
    
    # Add some unrelated events to test semantic filtering
    unrelated_events = [
        "The weather outside was sunny",
        "A bird flew past the window", 
        "The user received an email notification"
    ]
    
    for event in unrelated_events:
        print(f"   📝 Adding unrelated event: {event}")
        memory.add_event(event)
    
    # Query should still find relevant context despite unrelated events
    print(f"\n   🔍 Query: What was the sequence of file operations?")
    context = memory.get_context("What was the sequence of file operations?")
    print(f"   📖 Context (should focus on file operations, not weather/birds):")
    print(f"   {context}")
    
    print("\n5. Testing edge cases...")
    
    # Test query with no relevant context
    print(f"   🔍 Query about something not in memory: How do I bake a cake?")
    context = memory.get_context("How do I bake a cake?")
    print(f"   📖 Context: {context}")
    
    # Clean up
    print("\n6. Cleaning up...")
    memory.close()
    print("✅ Memory core closed successfully!")
    
    print("\n🎉 Example completed successfully!")
    print("\nThe Causal Memory Core has demonstrated:")
    print("- ✅ Automatic causal relationship detection")
    print("- ✅ Semantic similarity matching") 
    print("- ✅ Narrative chain reconstruction")
    print("- ✅ Context-aware query responses")
    print("- ✅ Filtering of irrelevant information")

if __name__ == "__main__":
    main()
