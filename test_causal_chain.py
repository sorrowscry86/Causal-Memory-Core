from src.causal_memory_core import CausalMemoryCore
from test_config import TestConfig

# Initialize the memory core with the test config
memory = CausalMemoryCore(db_path=TestConfig.DB_PATH)
memory.config = TestConfig

# Add the first event
memory.add_event("The power went out.")

# Add the second event, which is caused by the first
memory.add_event("The computer turned off.")

# Define a query for the second event
query = "Why did the computer turn off?"

# Get the context for the query
context = memory.get_context(query)

# Print the context
print(context)

# Close the connection
memory.close()