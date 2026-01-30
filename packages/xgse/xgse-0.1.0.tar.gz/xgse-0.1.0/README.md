# XGSE: Extreme General Skill Engine 
## Overview
- The General Skill Engine is **Implementation** of [Anthropic-Agent-Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) Protocol
- To empower your AI agents with a modular skill framework that supports dynamic skill discovery, progressive context loading, planning, and task execution.
- The Agent Skills Framework implements a multi-level progressive context loading mechanism that efficiently manages skill discovery and execution:
1. **Level 1 (Metadata)**: Load all skill names and descriptions
2. **Level 2 (Retrieval)**: Retrieve and load SKILL.md when relevant with the query
3. **Level 3 (Resources)**: Load additional files (references, scripts, resources) only when referenced in SKILL.md
4. **Level 4 (Analysis|Planning|Execution)**: Analyze the loaded skill context, plan the execution steps, and run the necessary scripts

This approach minimizes resource consumption while providing comprehensive skill capabilities.


## XGSE Features
- 📜 **Standard Skill Protocol**: Fully compatible with the [Anthropic Skills](https://github.com/anthropics/skills) protocol
- 🧠 **Heuristic Context Loading**: Loads only necessary context—such as `References`, `Resources`, and `Scripts` on demand
- 🤖 **Autonomous Execution**: Agents autonomously analyze, plan, and decide which scripts and resources to execute based on skill definitions
- 🔍 **Skill Management**: Supports batch loading of skills and can automatically retrieve and discover relevant skills based on user input
- 🛡️ **Code Execution Environment**: Optional local direct code execution or secure sandboxed (E2B...) execution, with automatic dependency installation and environment isolation
- 📁 **Multi-file Type Support**: Supports documentation, scripts, and resource files
- 🧩 **Extensible Design**: The skill data structure is modularized, with implementations such as `SkillSchema` and `SkillContext` provided for easy extension and customization


## Run Skill Prerequisites
- If Execution code on localhost with uv command, must install 'pip' in .venv:
```bash
  source ".venv/bin/activate"
  python -m ensurepip --upgrade 
```
- Use E2B Sandbox, must config 'E2B_API_KEY' in env
- Use LiteLLM, must config 'LLM_API_KEY' in env
- Can use [OpenSkill](https://github.com/numman-ali/openskills) download Claude skills to local

## Examples
- skill: Run skill on local host or sandbox