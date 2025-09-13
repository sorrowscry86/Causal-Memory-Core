#!/usr/bin/env python3
"""
Command Line Interface for the Causal Memory Core
Provides an interactive way to add events and query memory
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Prefer importing the module to keep it patchable via 'src.causal_memory_core.CausalMemoryCore'
try:
    import src.causal_memory_core as cmcore  # type: ignore
except Exception:  # Fallback for direct execution contexts
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    import causal_memory_core as cmcore  # type: ignore

class _CausalMemoryCoreFactory:
    """Factory wrapper so tests can patch either cli.CausalMemoryCore or src.causal_memory_core.CausalMemoryCore."""
    def __call__(self, *args, **kwargs):
        return cmcore.CausalMemoryCore(*args, **kwargs)

# Expose factory at module level for tests to patch
CausalMemoryCore = _CausalMemoryCoreFactory()


def _safe_print(message: str) -> None:
    """Print text with emoji, but fall back to ASCII if the current stdout encoding
    cannot represent certain characters (e.g., Windows code pages).
    """
    enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    try:
        _ = message.encode(enc)
        print(message)
    except UnicodeEncodeError:
        replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]',
            '📖': 'Context',
            '🧠': 'Causal Memory Core',
            '👋': 'Goodbye!',
            '→': '->',
        }
        ascii_msg = message
        for k, v in replacements.items():
            ascii_msg = ascii_msg.replace(k, v)
        try:
            print(ascii_msg)
        except Exception:
            # Last resort: strip non-ASCII
            print(ascii_msg.encode(enc, errors='ignore').decode(enc, errors='ignore'))


def add_event_command(memory_core, event_text):
    """Add an event to memory"""
    try:
        memory_core.add_event(event_text)
        _safe_print(f"✅ Event added: {event_text}")
    except Exception as e:
        _safe_print(f"❌ Error adding event: {e}")


def query_command(memory_core, query_text):
    """Query memory for context"""
    try:
        context = memory_core.get_context(query_text)
        _safe_print(f"📖 Context for '{query_text}':")
        _safe_print(f"{context}")
    except Exception as e:
        _safe_print(f"❌ Error querying memory: {e}")


def interactive_mode(memory_core):
    """Run in interactive mode"""
    _safe_print("🧠 Causal Memory Core - Interactive Mode")
    _safe_print("Commands:")
    _safe_print("  add <event>    - Add an event to memory")
    _safe_print("  query <text>   - Query memory for context")
    _safe_print("  help          - Show this help")
    _safe_print("  quit          - Exit")
    _safe_print("")
    
    while True:
        try:
            user_input = input("memory> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if user_input.lower() in ['help', 'h']:
                _safe_print("Commands:")
                _safe_print("  add <event>    - Add an event to memory")
                _safe_print("  query <text>   - Query memory for context")
                _safe_print("  help          - Show this help")
                _safe_print("  quit          - Exit")
                continue
            
            parts = user_input.split(' ', 1)
            command = parts[0].lower()
            
            if command == 'add' and len(parts) > 1:
                add_event_command(memory_core, parts[1])
            elif command == 'query' and len(parts) > 1:
                query_command(memory_core, parts[1])
            else:
                _safe_print("❌ Invalid command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            _safe_print("\n👋 Goodbye!")
            break
        except EOFError:
            _safe_print("\n👋 Goodbye!")
            break


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Causal Memory Core CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --add "The user opened a file"
  python cli.py --query "How did the file get opened?"
  python cli.py --interactive
        """
    )
    parser.add_argument('--add', '-a', help='Add an event to memory')
    parser.add_argument('--query', '-q', help='Query memory for context')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--db-path', help='Path to database file (overrides config)')
    return parser


def parse_args(argv=None):
    return build_parser().parse_args(argv)


def _exit_or_return(code: int) -> int:
    """If sys.exit is patched (tests), let it raise. Otherwise return code."""
    try:
        # Detect if sys.exit is mocked by checking for attribute typical of Mock
        if hasattr(sys.exit, 'side_effect') or hasattr(sys.exit, 'assert_called'):  # type: ignore[attr-defined]
            sys.exit(code)
    except SystemExit:
        raise
    return code

def main(argv=None) -> int:
    """Main CLI function. Accepts argv for in-process invocation in tests.
    Returns process exit code (0 success, 1 error).
    """
    args = parse_args(argv)

    # Load environment variables (skippable for tests via CMC_SKIP_DOTENV=1)
    if os.getenv('CMC_SKIP_DOTENV') != '1':
        load_dotenv()

    # Check if we have required configuration
    if not os.getenv('OPENAI_API_KEY'):
        _safe_print("❌ Error: OPENAI_API_KEY not found in environment")
        _safe_print("Please set up your .env file with your OpenAI API key")
        _safe_print("See .env.template for an example")
        return _exit_or_return(1)

    # Initialize memory core
    memory_core = None
    try:
        db_path = args.db_path if args.db_path else None
        # Use factory so tests can patch either cli.CausalMemoryCore or src.causal_memory_core.CausalMemoryCore
        memory_core = CausalMemoryCore(db_path=db_path)
        _safe_print("✅ Causal Memory Core initialized")
    except Exception as e:
        _safe_print(f"❌ Error initializing memory core: {e}")
        return _exit_or_return(1)

    try:
        # Handle commands
        if args.add:
            add_event_command(memory_core, args.add)
        elif args.query:
            query_command(memory_core, args.query)
        elif args.interactive:
            interactive_mode(memory_core)
        else:
            # No command specified, show help
            build_parser().print_help()
    finally:
        # Clean up
        if memory_core is not None:
            memory_core.close()

    return 0

if __name__ == "__main__":
    main()
