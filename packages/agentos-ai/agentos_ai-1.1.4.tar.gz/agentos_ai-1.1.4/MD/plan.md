# AgentOS – MVP Spec (Phase 1)

## 🎯 Goal

Deliver a **minimal but magical runtime** that lets any developer:

1. Install AgentOS quickly (`pip install agentos` or binary download).
2. Define an agent in a simple **manifest file**.
3. Run it with **memory + safe tool sandboxing** out of the box.
4. See clear value beyond just using LangChain/Docker.

---

## 🏗 MVP Components

### 1. CLI + Daemon

- `agentos run <agent>` → runs an agent from manifest.
- `agentos ps` → list running agents.
- `agentos logs <agent>` → tail logs.
- Daemon handles lifecycle and isolates agents.

### 2. Agent Manifest (YAML/JSON)

Minimal format:

```yaml
name: research_assistant
model: openai:gpt-4o
memory: local
tools:
  - python_exec
  - web_browse
```

### 3. Memory Service

- Default: **SQLite + embeddings** (runs locally, no config).
- API: `agent.memory.store()` and `agent.memory.search()`.

### 4. Tool Sandbox

- **Safe execution layer** for built-in tools:

  - `python_exec` (restricted subprocess)
  - `web_browse` (headless fetch + scrape)

- Future tools can be added, but MVP only ships 2.

### 5. Model Router (Basic)

- `--model local` → use bundled small model (Mistral 7B quantized).
- `--model openai:gpt-4o` → API call.
- Smart routing not needed yet, just basic selection.

### 6. Logging & Monitoring

- Standard logs written to `~/.agentos/logs/<agent>.log`.
- Simple JSON output for integration.

---

## 🚀 Example Workflow

1. Developer installs runtime:

```bash
pip install agentos
```

2. Creates `agent.yaml`:

```yaml
name: hello_agent
model: local
memory: local
tools:
  - python_exec
```

3. Runs task:

```bash
agentos run hello_agent --task "Write a Python script that prints prime numbers up to 100"
```

4. Output:

- Agent calls `python_exec` tool.
- Stores result in memory.
- Developer can query memory with:

```bash
agentos logs hello_agent
```

---

## 🛠 Out of Scope for MVP

- Agent Hub (push/pull registry).
- Orchestration (multi-agent).
- Full OS/distro.
- Enterprise IAM/DLP.

---

## ✅ Success Criteria

- Installation < 5 minutes.
- First agent runs with **memory + sandboxed tool** without extra config.
- Developers feel: _“This is easier and safer than hacking LangChain + Docker myself.”_

---

## 🔜 Next Step (Post-MVP)

- Add **Agent Hub** for sharing manifests.
- Expand **tool library** (browser automation, DB connectors).
- Introduce **basic orchestrator** (multi-agent YAML).
