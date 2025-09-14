#!/usr/bin/env python3
"""
Database Inspection Utility for Causal Memory Core
Provides tools to inspect database state, embeddings, and similarity calculations
"""

import sys
import os
import argparse
import numpy as np
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from causal_memory_core import CausalMemoryCore, Event
import duckdb


class DatabaseInspector:
    """Utility for inspecting Causal Memory Core database state"""
    
    def __init__(self, db_path: str = 'causal_memory.db'):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def list_all_events(self):
        """List all events in the database"""
        try:
            result = self.conn.execute("""
                SELECT event_id, timestamp, effect_text, cause_id, relationship_text
                FROM events 
                ORDER BY timestamp ASC
            """).fetchall()
            
            print(f"📊 Total Events: {len(result)}")
            print("=" * 80)
            
            for row in result:
                event_id, timestamp, effect_text, cause_id, relationship_text = row
                print(f"🔗 Event {event_id}: {effect_text}")
                print(f"   📅 Time: {timestamp}")
                if cause_id:
                    print(f"   ⬅️  Caused by: Event {cause_id}")
                    if relationship_text:
                        print(f"   📝 Relationship: {relationship_text}")
                else:
                    print(f"   🎯 Root event (no cause)")
                print()
                
        except Exception as e:
            print(f"❌ Error listing events: {e}")
            
    def show_causal_chains(self):
        """Show all causal chains in the database"""
        try:
            # Find root events (no cause)
            roots = self.conn.execute("""
                SELECT event_id, effect_text FROM events WHERE cause_id IS NULL
            """).fetchall()
            
            print(f"🌳 Causal Chains ({len(roots)} root events)")
            print("=" * 80)
            
            for root_id, root_text in roots:
                print(f"🎯 Root: {root_text} (ID: {root_id})")
                self._print_chain_from_root(root_id, indent=1)
                print()
                
        except Exception as e:
            print(f"❌ Error showing causal chains: {e}")
            
    def _print_chain_from_root(self, event_id: int, indent: int = 0):
        """Recursively print causal chain from a root event"""
        try:
            # Find events caused by this event
            children = self.conn.execute("""
                SELECT event_id, effect_text, relationship_text
                FROM events 
                WHERE cause_id = ?
                ORDER BY timestamp ASC
            """, [event_id]).fetchall()
            
            for child_id, child_text, relationship in children:
                prefix = "  " * indent + "⬇️  "
                print(f"{prefix}{child_text} (ID: {child_id})")
                if relationship:
                    print(f"{prefix}   📝 {relationship}")
                
                # Recursively print children of this child
                self._print_chain_from_root(child_id, indent + 1)
                
        except Exception as e:
            print(f"❌ Error printing chain: {e}")
            
    def analyze_embeddings(self):
        """Analyze embedding quality and distribution"""
        try:
            result = self.conn.execute("""
                SELECT event_id, effect_text, embedding
                FROM events
            """).fetchall()
            
            if not result:
                print("📊 No events found in database")
                return
                
            print(f"🧮 Embedding Analysis ({len(result)} events)")
            print("=" * 80)
            
            embeddings = []
            for event_id, effect_text, embedding in result:
                emb_array = np.array(embedding)
                embeddings.append(emb_array)
                
                print(f"🔗 Event {event_id}: {effect_text}")
                print(f"   📏 Dimension: {len(emb_array)}")
                print(f"   📊 Norm: {np.linalg.norm(emb_array):.3f}")
                print(f"   📈 Mean: {np.mean(emb_array):.3f}")
                print(f"   📉 Std: {np.std(emb_array):.3f}")
                print()
                
            if len(embeddings) > 1:
                print("🔄 Pairwise Similarities:")
                print("-" * 40)
                
                for i in range(len(embeddings)):
                    for j in range(i + 1, len(embeddings)):
                        similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                        event_i_text = result[i][1][:30] + "..." if len(result[i][1]) > 30 else result[i][1]
                        event_j_text = result[j][1][:30] + "..." if len(result[j][1]) > 30 else result[j][1]
                        print(f"  {i+1} ↔ {j+1}: {similarity:.3f} | {event_i_text} ↔ {event_j_text}")
                        
        except Exception as e:
            print(f"❌ Error analyzing embeddings: {e}")
            
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
        
    def test_similarity_search(self, query_text: str):
        """Test similarity search for a given query"""
        try:
            print(f"🔍 Testing similarity search for: '{query_text}'")
            print("=" * 80)
            
            # Create a temporary memory core to use embedder
            from config import Config
            memory_core = CausalMemoryCore(db_path=self.db_path)
            
            # Generate query embedding
            query_embedding = memory_core.embedder.encode(query_text).tolist()
            query_array = np.array(query_embedding)
            
            print(f"📏 Query embedding dimension: {len(query_embedding)}")
            print(f"📊 Query embedding norm: {np.linalg.norm(query_array):.3f}")
            print()
            
            # Get all events and calculate similarities
            result = self.conn.execute("""
                SELECT event_id, effect_text, embedding
                FROM events
            """).fetchall()
            
            similarities = []
            for event_id, effect_text, embedding in result:
                event_array = np.array(embedding)
                similarity = self._cosine_similarity(query_array, event_array)
                similarities.append((similarity, event_id, effect_text))
                
            # Sort by similarity
            similarities.sort(reverse=True)
            
            print(f"🎯 Similarity Rankings (threshold: {Config.SIMILARITY_THRESHOLD}):")
            print("-" * 60)
            
            for similarity, event_id, effect_text in similarities:
                status = "✅ MATCH" if similarity >= Config.SIMILARITY_THRESHOLD else "❌ BELOW"
                print(f"{similarity:.3f} {status} | Event {event_id}: {effect_text}")
                
            # Test get_context
            print("\n🔮 Context Retrieval Test:")
            print("-" * 30)
            context = memory_core.get_context(query_text)
            print(context)
            
            memory_core.close()
            
        except Exception as e:
            print(f"❌ Error testing similarity search: {e}")
            
    def database_stats(self):
        """Show database statistics"""
        try:
            print("📈 Database Statistics")
            print("=" * 50)
            
            # Event count
            total_events = self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            print(f"Total Events: {total_events}")
            
            # Root events (no cause)
            root_events = self.conn.execute("SELECT COUNT(*) FROM events WHERE cause_id IS NULL").fetchone()[0]
            print(f"Root Events: {root_events}")
            
            # Events with causes
            caused_events = total_events - root_events
            print(f"Events with Causes: {caused_events}")
            
            if total_events > 0:
                print(f"Causality Ratio: {caused_events/total_events:.1%}")
                
            # Date range
            date_range = self.conn.execute("""
                SELECT MIN(timestamp), MAX(timestamp) FROM events
            """).fetchone()
            
            if date_range[0]:
                print(f"Date Range: {date_range[0]} to {date_range[1]}")
                
            # Check for broken chains
            broken_chains = self.conn.execute("""
                SELECT COUNT(*) FROM events e1
                WHERE e1.cause_id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM events e2 WHERE e2.event_id = e1.cause_id)
            """).fetchone()[0]
            
            if broken_chains > 0:
                print(f"⚠️  Broken Chains: {broken_chains}")
            else:
                print("✅ No Broken Chains")
                
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")


def main():
    """Command line interface for database inspection"""
    parser = argparse.ArgumentParser(description='Inspect Causal Memory Core database')
    parser.add_argument('--db', default='causal_memory.db', help='Database file path')
    parser.add_argument('--list', action='store_true', help='List all events')
    parser.add_argument('--chains', action='store_true', help='Show causal chains')
    parser.add_argument('--embeddings', action='store_true', help='Analyze embeddings')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--search', type=str, help='Test similarity search for given query')
    parser.add_argument('--all', action='store_true', help='Run all analyses')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"❌ Database file not found: {args.db}")
        return
        
    inspector = DatabaseInspector(args.db)
    
    try:
        if args.all or args.stats:
            inspector.database_stats()
            print()
            
        if args.all or args.list:
            inspector.list_all_events()
            print()
            
        if args.all or args.chains:
            inspector.show_causal_chains()
            print()
            
        if args.all or args.embeddings:
            inspector.analyze_embeddings()
            print()
            
        if args.search:
            inspector.test_similarity_search(args.search)
            
        if not any([args.list, args.chains, args.embeddings, args.stats, args.search, args.all]):
            print("🧠 Causal Memory Core - Database Inspector")
            print("Use --help for available options")
            print("Quick start: python db_inspector.py --all")
            
    finally:
        inspector.close()


if __name__ == '__main__':
    main()