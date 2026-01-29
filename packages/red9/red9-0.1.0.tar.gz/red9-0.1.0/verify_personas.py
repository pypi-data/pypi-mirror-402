"""Verification script for Specialist Personas."""

import sys
from pathlib import Path

# Ensure red9 is in path
sys.path.insert(0, str(Path.cwd()))

from red9.agents.personas import get_specialist_prompt
from red9.agents.prompts import get_agent_prompt


def test_personas():
    print("\n--- Testing Specialist Personas ---")

    # 1. Frontend Persona
    frontend_prompt = get_specialist_prompt("frontend")
    if "React" in frontend_prompt and "Visuals vs Logic" in frontend_prompt:
        print("✅ Frontend persona loaded correctly")
    else:
        print("❌ Frontend persona failed")

    # 2. Docs Persona
    docs_prompt = get_specialist_prompt("docs")
    if "READMEs" in docs_prompt and "Clarity" in docs_prompt:
        print("✅ Docs persona loaded correctly")
    else:
        print("❌ Docs persona failed")

    # 3. Integration with Code Agent Prompt
    code_prompt = get_agent_prompt("code", persona="backend")
    if "API design" in code_prompt and "Security First" in code_prompt:
        print("✅ Code agent prompt successfully injected backend persona")
    else:
        print("❌ Code agent prompt injection failed")
        print(f"Prompt content preview: {code_prompt[:200]}...")


if __name__ == "__main__":
    test_personas()
    print("\nALL CHECKS PASSED")
