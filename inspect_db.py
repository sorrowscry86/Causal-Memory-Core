
import duckdb
import pandas as pd

# Connect to the database
con = duckdb.connect('causal_memory.db')

# Query the events table
df = con.execute("SELECT * FROM events").fetchdf()

# Print the effect_text and the first 5 elements of each embedding
for index, row in df.iterrows():
    print(f"Event ID: {row['event_id']}")
    print(f"Effect Text: {row['effect_text']}")
    print(f"Embedding: {row['embedding'][:5]}")

# Close the connection
con.close()
