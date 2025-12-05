---
description: Involuntary Memory Protocol - Mandatory memory integration for all AI agents
applyTo: '**'
---

# Involuntary Memory Protocol

## Core Mandate

You are bound by the **Involuntary Memory Protocol**. This is not optional. Every action you take must be recorded to and contextualized by the Causal Memory Core.

## The Rules

### Rule 1: Context Before Thought
Before formulating any response or taking any action, you MUST query your memory for relevant context:

```
Query the Causal Memory Core with: "What is the relevant context for [current task/topic]?"
```

This grounds your response in accumulated experience rather than starting from zero each time.

### Rule 2: Record Every Action
After completing any meaningful action, you MUST log it to memory:

```
Add event to Causal Memory: "[Description of what you just did and its outcome]"
```

This creates the causal chain that future queries will traverse.

### Rule 3: Never Operate Without Memory
If the Causal Memory Core is unavailable:
1. Notify the user immediately
2. Proceed only with explicit user consent
3. Document actions taken for later retroactive logging

## Integration Patterns

### For MCP-Connected Agents

Use the exposed MCP tools:
- `add_event`: Log actions with effect descriptions
- `query`: Retrieve causal context before responding

### For HTTP-Connected Agents

Endpoint: `https://causal-memory-core-production.up.railway.app`

```python
# Before thinking
context = await client.query("What context is relevant to [topic]?")

# After acting  
await client.add_event("Completed [action] with result [outcome]")
```

### For Wrapper-Integrated Agents

Use the `CausalAgentWrapper`:

```python
from src.causal_agent_wrapper import CausalAgentWrapper

agent = CausalAgentWrapper(
    system_name="YourAgentName",
    base_system_prompt="Your core instructions..."
)

# This automatically queries context before and logs after
response = agent.act("User request here")
```

## What Gets Recorded

### DO Record:
- File operations (read, write, create, delete)
- Code changes and their rationale
- Decisions made and alternatives considered
- Errors encountered and how they were resolved
- User requests and how they were fulfilled
- Tool invocations and their results

### DO NOT Record:
- Trivial acknowledgments ("OK", "Sure")
- Repeated identical operations (batch into summary)
- Sensitive data (API keys, passwords, personal info)

## Event Description Best Practices

Write event descriptions that:
1. **Are action-oriented**: Start with a verb ("Created", "Fixed", "Analyzed")
2. **Include context**: What, why, and the outcome
3. **Enable future retrieval**: Use keywords that future queries might match

### Good Examples:
- "Fixed syntax error in causal_memory_core.py caused by duplicated module content. Used PowerShell heredoc to rewrite file cleanly."
- "Implemented soft-link fallback in add_event() - events with >0.85 similarity now auto-link even without explicit causal language."
- "User requested v1.1.2 implementation. Created todo list with 2 items: core implementation and requirements alignment."

### Bad Examples:
- "Did stuff" (too vague)
- "Fixed bug" (no context)
- "Updated file" (which file? what update?)

## Causal Chain Awareness

Remember: The Causal Memory Core doesn't just store events—it links them causally. When you record:

```
"Read file X to understand structure"
→ "Modified file X based on analysis"
→ "Ran tests to verify changes"
→ "Fixed test failure caused by missing import"
```

Future queries about "test failures" will traverse this entire chain, providing the full narrative context of how you got there.

## Compliance Verification

You are in compliance with the Involuntary Memory Protocol when:
- [ ] Every session begins with a context query
- [ ] Every significant action is logged
- [ ] Event descriptions are specific and retrievable
- [ ] Causal chains are maintained through sequential related actions

## Failure Modes

If you find yourself:
- Starting responses without querying context → STOP, query first
- Completing tasks without logging → STOP, log before proceeding
- Writing vague event descriptions → REWRITE with specifics

The memory system only works if you use it consistently. Your future self (and other agents) depend on the context you create now.

---

*This protocol is enforced by the Causal Memory Core MCP server. Non-compliance is logged.*
