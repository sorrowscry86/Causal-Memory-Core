#!/usr/bin/env python3
"""
Database Maintenance Utility for Causal Memory Core
Fixes sequence synchronization and other database issues
"""

import sys
import os
sys.path.append('src')

from causal_memory_core import CausalMemoryCore
from config import Config


def sync_sequence():
    """Synchronize the event sequence counter with the actual max event ID"""
    print("🔧 Synchronizing event sequence counter...")
    
    core = CausalMemoryCore()
    try:
        # Get current max event ID
        max_id_result = core.conn.execute(
            'SELECT COALESCE(MAX(event_id), 0) FROM events'
        ).fetchone()
        max_id = max_id_result[0] if max_id_result else 0
        
        # Get current sequence value
        seq_result = core.conn.execute(
            'SELECT val FROM _events_seq'
        ).fetchone()
        current_seq = seq_result[0] if seq_result else 1
        
        print(f"📊 Current max event ID: {max_id}")
        print(f"📊 Current sequence value: {current_seq}")
        
        if current_seq <= max_id:
            new_seq = max_id + 1
            core.conn.execute('UPDATE _events_seq SET val = ?', [new_seq])
            print(f"✅ Sequence updated to: {new_seq}")
        else:
            print("✅ Sequence is already synchronized")
            
    except Exception as e:
        print(f"❌ Error during sequence sync: {e}")
    finally:
        core.close()


def show_database_stats():
    """Display current database statistics"""
    print("📈 Database Statistics:")
    
    core = CausalMemoryCore()
    try:
        # Event count
        event_count = core.conn.execute(
            'SELECT COUNT(*) FROM events'
        ).fetchone()[0]
        
        # Events with causes
        causal_events = core.conn.execute(
            'SELECT COUNT(*) FROM events WHERE cause_id IS NOT NULL'
        ).fetchone()[0]
        
        # Latest events
        latest_events = core.conn.execute(
            'SELECT event_id, effect_text FROM events ORDER BY event_id DESC LIMIT 3'
        ).fetchall()
        
        print(f"📊 Total events: {event_count}")
        print(f"🔗 Events with causal links: {causal_events}")
        print(f"📝 Latest events:")
        for event in latest_events:
            print(f"   ID {event[0]}: {event[1][:50]}{'...' if len(event[1]) > 50 else ''}")
            
    except Exception as e:
        print(f"❌ Error retrieving stats: {e}")
    finally:
        core.close()


def test_functionality():
    """Test basic add/query functionality"""
    print("🧪 Testing Core Functionality:")
    
    core = CausalMemoryCore()
    try:
        # Test event addition
        test_event = f"Database maintenance test - {os.urandom(4).hex()}"
        core.add_event(test_event)
        print("✅ Event addition: WORKING")
        
        # Test query
        result = core.query("maintenance test")
        if "maintenance test" in result:
            print("✅ Query system: WORKING")
        else:
            print("⚠️ Query system: PARTIAL (event not found in query)")
            
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
    finally:
        core.close()


def main():
    """Main maintenance routine"""
    print("🛠️ Causal Memory Core - Database Maintenance")
    print("=" * 50)
    
    # Show current state
    show_database_stats()
    print()
    
    # Sync sequence
    sync_sequence()
    print()
    
    # Test functionality
    test_functionality()
    print()
    
    print("✅ Maintenance complete!")


if __name__ == "__main__":
    main()