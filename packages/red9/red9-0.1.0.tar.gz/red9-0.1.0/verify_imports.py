import os
import sys

# Add current dir to path
sys.path.insert(0, os.getcwd())

print("Checking imports...")

try:
    print("1. Checking Repomap...")
    from red9.indexing.repomap.generator import RepoMap

    print("   ✅ RepoMap imported")
except ImportError as e:
    print(f"   ❌ RepoMap Failed: {e}")

try:
    print("2. Checking Quality Gates...")
    from red9.quality.gates import QualityGate, QualityResult, check_quality_gates

    print("   ✅ Quality Gates imported")
except ImportError as e:
    print(f"   ❌ Quality Gates Failed: {e}")

try:
    print("3. Checking Personas...")
    from red9.agents.personas import ArchitectPersona, get_specialist_prompt

    print("   ✅ Personas imported")
except ImportError as e:
    print(f"   ❌ Personas Failed: {e}")

try:
    print("4. Checking Simple Code Task...")
    from red9.agents.tasks.simple_code import SimpleCodeAgentTask

    print("   ✅ SimpleCodeAgentTask imported")
except ImportError as e:
    print(f"   ❌ SimpleCodeAgentTask Failed: {e}")

try:
    print("5. Checking Iteration Loop...")
    from red9.agents.tasks.iteration_loop import IterationLoopTask

    print("   ✅ IterationLoopTask imported")
except ImportError as e:
    print(f"   ❌ IterationLoopTask Failed: {e}")
