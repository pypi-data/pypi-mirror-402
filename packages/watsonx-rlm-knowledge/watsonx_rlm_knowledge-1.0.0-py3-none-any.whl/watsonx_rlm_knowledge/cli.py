"""
RLM Knowledge Client CLI

Command-line interface for the RLM-based knowledge client.

Usage:
    # Query knowledge base
    rlm-knowledge query "How does authentication work?"
    
    # Interactive chat mode
    rlm-knowledge chat
    
    # List documents
    rlm-knowledge list
    
    # Search documents
    rlm-knowledge search "authentication"
    
    # Preprocess documents
    rlm-knowledge preprocess
    
    # Show statistics
    rlm-knowledge stats
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_client(knowledge_root: Optional[str] = None, verbose: bool = False):
    """Get a configured KnowledgeClient."""
    from watsonx_rlm_knowledge import KnowledgeClient
    from watsonx_rlm_knowledge.exceptions import ConfigurationError
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get knowledge root
    if knowledge_root is None:
        knowledge_root = os.environ.get("RLM_KNOWLEDGE_ROOT")
    
    if not knowledge_root:
        print("Error: Knowledge root not specified.", file=sys.stderr)
        print("Set RLM_KNOWLEDGE_ROOT environment variable or use --knowledge-root", file=sys.stderr)
        sys.exit(1)
    
    if not Path(knowledge_root).exists():
        print(f"Error: Knowledge root does not exist: {knowledge_root}", file=sys.stderr)
        sys.exit(1)
    
    try:
        return KnowledgeClient.from_directory(knowledge_root)
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error initializing client: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_query(args):
    """Handle query command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    question = " ".join(args.question)
    
    if args.detailed:
        result = client.query_detailed(question)
        print(f"\n{'='*60}")
        print("ANSWER:")
        print(f"{'='*60}")
        print(result.answer)
        print(f"\n{'='*60}")
        print("METADATA:")
        print(f"{'='*60}")
        print(f"  Iterations: {result.iterations}")
        print(f"  Time: {result.total_time:.2f}s")
        print(f"  Success: {result.success}")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
            if args.verbose:
                for err in result.errors:
                    print(f"    - {err[:100]}")
    else:
        answer = client.query(question)
        print(answer)
    
    client.cleanup()


def cmd_chat(args):
    """Handle interactive chat command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    print("RLM Knowledge Chat")
    print("Type 'quit' or 'exit' to stop, 'help' for commands")
    print(f"Knowledge root: {client.knowledge.root}")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        lower_input = user_input.lower()
        
        if lower_input in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        
        if lower_input == "help":
            print("\nCommands:")
            print("  quit/exit - Exit chat")
            print("  help - Show this help")
            print("  /list - List documents")
            print("  /search <term> - Search documents")
            print("  /stats - Show statistics")
            print("  <question> - Ask about the knowledge base")
            continue
        
        if lower_input == "/list":
            docs = client.list_documents()
            print(f"\nDocuments ({len(docs)}):")
            for doc in docs[:20]:
                print(f"  - {doc}")
            if len(docs) > 20:
                print(f"  ... and {len(docs) - 20} more")
            continue
        
        if lower_input.startswith("/search "):
            term = user_input[8:].strip()
            if term:
                results = client.search(term, max_results=10)
                print(f"\nSearch results for '{term}' ({len(results)} matches):")
                for r in results:
                    print(f"  {r['path']}:{r['line']}: {r['text'][:60]}...")
            continue
        
        if lower_input == "/stats":
            stats = client.get_stats()
            print("\nKnowledge Base Statistics:")
            print(f"  Documents: {stats['document_count']}")
            print(f"  Total size: {stats['total_size_mb']} MB")
            print(f"  Text size: {stats['text_size_mb']} MB")
            print(f"  Formats: {stats['formats']}")
            continue
        
        # Query the knowledge base
        print("\nAssistant: ", end="", flush=True)
        try:
            answer = client.query(user_input)
            print(answer)
        except Exception as e:
            print(f"Error: {e}")
    
    client.cleanup()


def cmd_list(args):
    """Handle list command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    docs = client.list_documents(pattern=args.pattern)
    
    if args.json:
        print(json.dumps(docs, indent=2))
    else:
        print(f"Documents in knowledge base ({len(docs)}):")
        for doc in docs:
            print(f"  {doc}")
    
    client.cleanup()


def cmd_search(args):
    """Handle search command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    term = " ".join(args.term)
    results = client.search(term, max_results=args.max_results)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Search results for '{term}' ({len(results)} matches):")
        for r in results:
            print(f"  {r['path']}:{r['line']}: {r['text']}")
    
    client.cleanup()


def cmd_preprocess(args):
    """Handle preprocess command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    print(f"Preprocessing documents in {client.knowledge.root}...")
    count = client.preprocess(force=args.force)
    print(f"Processed {count} documents")
    
    client.cleanup()


def cmd_stats(args):
    """Handle stats command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    stats = client.get_stats()
    
    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print("Knowledge Base Statistics")
        print("=" * 40)
        print(f"Root: {stats['knowledge_root']}")
        print(f"Documents: {stats['document_count']}")
        print(f"Total size: {stats['total_size_mb']} MB")
        print(f"Text size: {stats['text_size_mb']} MB")
        print("\nFormats:")
        for fmt, count in sorted(stats['formats'].items()):
            print(f"  {fmt}: {count}")
    
    client.cleanup()


def cmd_read(args):
    """Handle read command."""
    client = get_client(args.knowledge_root, args.verbose)
    
    try:
        content = client.read_document(args.path, max_bytes=args.max_bytes)
        print(content)
    except Exception as e:
        print(f"Error reading document: {e}", file=sys.stderr)
        sys.exit(1)
    
    client.cleanup()


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="RLM Knowledge Client - Query your documents with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query the knowledge base
  rlm-knowledge query "How does the authentication system work?"
  
  # Interactive chat
  rlm-knowledge chat
  
  # List all documents
  rlm-knowledge list
  
  # Search for a term
  rlm-knowledge search "database schema"
  
  # Preprocess documents
  rlm-knowledge preprocess
  
  # Show statistics
  rlm-knowledge stats

Environment Variables:
  WATSONX_API_KEY        - IBM Cloud API key (required)
  WATSONX_PROJECT_ID     - WatsonX project ID (required)
  WATSONX_REGION_URL     - Region URL (default: us-south)
  WATSONX_MODEL_ID       - Model ID (default: openai/gpt-oss-120b)
  RLM_KNOWLEDGE_ROOT     - Default knowledge directory
        """
    )
    
    # Global arguments
    parser.add_argument(
        "--knowledge-root", "-k",
        help="Path to knowledge directory (or set RLM_KNOWLEDGE_ROOT)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the knowledge base"
    )
    query_parser.add_argument(
        "question",
        nargs="+",
        help="Question to ask"
    )
    query_parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Show detailed result with metadata"
    )
    query_parser.set_defaults(func=cmd_query)
    
    # Chat command
    chat_parser = subparsers.add_parser(
        "chat",
        help="Interactive chat mode"
    )
    chat_parser.set_defaults(func=cmd_chat)
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List documents in knowledge base"
    )
    list_parser.add_argument(
        "--pattern", "-p",
        help="Glob pattern to filter (e.g., '*.pdf')"
    )
    list_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    list_parser.set_defaults(func=cmd_list)
    
    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search documents for a term"
    )
    search_parser.add_argument(
        "term",
        nargs="+",
        help="Search term"
    )
    search_parser.add_argument(
        "--max-results", "-m",
        type=int,
        default=20,
        help="Maximum results (default: 20)"
    )
    search_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    search_parser.set_defaults(func=cmd_search)
    
    # Preprocess command
    preprocess_parser = subparsers.add_parser(
        "preprocess",
        help="Preprocess documents (convert PDF, DOCX, etc.)"
    )
    preprocess_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force reprocessing of all documents"
    )
    preprocess_parser.set_defaults(func=cmd_preprocess)
    
    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show knowledge base statistics"
    )
    stats_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    stats_parser.set_defaults(func=cmd_stats)
    
    # Read command
    read_parser = subparsers.add_parser(
        "read",
        help="Read a document"
    )
    read_parser.add_argument(
        "path",
        help="Document path (relative to knowledge root)"
    )
    read_parser.add_argument(
        "--max-bytes", "-m",
        type=int,
        default=50000,
        help="Maximum bytes to read (default: 50000)"
    )
    read_parser.set_defaults(func=cmd_read)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Run the command
    args.func(args)


if __name__ == "__main__":
    main()
