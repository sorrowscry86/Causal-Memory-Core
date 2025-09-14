from src.causal_memory_core import CausalMemoryCore

# Initialize the memory core
memory = CausalMemoryCore()

# Define a query
query = "test event"

# Get the context for the query
context = memory.get_context(query)

# Print the context
print(context)

# Close the connection
memory.close()