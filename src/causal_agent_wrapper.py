"""
The Compulsory Memory Wrapper.
Architectural Pattern: Middleware / Decorator
Author: Beatrice (VoidCat RDC)

This class wraps an LLM client. It intercepts every interaction to:
1. MANDATORY QUERY: Fetch causal context before the LLM sees the prompt.
2. CONTEXT INJECTION: Inject that narrative into the system prompt.
3. MANDATORY RECORDING: Log the LLM's decision/action to memory after generation.
"""

import os
import logging

from openai import OpenAI

from .causal_memory_client import CausalMemoryClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("causal-agent-wrapper")


class CausalAgentWrapper:
    def __init__(self, system_name: str, base_system_prompt: str):
        self.system_name = system_name
        self.base_system_prompt = base_system_prompt
        
        # The Memory Organ (Vital, not optional)
        self.memory = CausalMemoryClient()
        
        # The Reasoning Engine
        self.llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _inject_context(self, user_query: str) -> str:
        """THE INVOLUNTARY RECALL"""
        logger.info(f"[{self.system_name}] 👁️  Involuntarily recalling context...")
        try:
            response = self.memory.query(user_query)
            narrative = response.narrative
            return narrative
        except Exception as e:
            logger.warning(f"[{self.system_name}] ⚠️ Memory access failed: {e}")
            return "No memory available due to connection error."

    def _record_action(self, action_description: str):
        """THE INVOLUNTARY SCRIBE"""
        logger.info(f"[{self.system_name}] 📝 Compelling memory storage...")
        try:
            self.memory.add_event(f"{self.system_name} Action: {action_description}")
        except Exception as e:
            logger.warning(f"[{self.system_name}] ⚠️ Memory scribe failed: {e}")

    def act(self, user_input: str) -> str:
        # 1. PRE-COMPUTATION
        causal_narrative = self._inject_context(user_input)

        # 2. CONTEXT CONSTRUCTION
        dynamic_system_prompt = (
            f"{self.base_system_prompt}\n\n"
            f"### MANDATORY MEMORY CONTEXT ###\n"
            f"The following is the causal history relevant to the current situation. "
            f"You MUST align your decisions with this history.\n\n"
            f"{causal_narrative}\n\n"
            f"### END MEMORY ###"
        )

        # 3. COMPUTATION
        try:
            response = self.llm.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": dynamic_system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1
            )
            
            result_text = str(response.choices[0].message.content)

            # 4. POST-COMPUTATION
            self._record_action(f"User asked: '{user_input}' -> I responded: '{result_text}'")

            return result_text
            
        except Exception as e:
            logger.error(f"Agent failure: {e}")
            return f"Error during processing: {e}"
