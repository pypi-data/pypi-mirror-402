---
title: Agent Memory Architecture
summary: Framework-independent patterns for managing agent conversation history and long-term memory—why prompt stuffing fails, state-managed alternatives, memory types, and multi-agent sharing.
topics:
  - memory-architecture
  - conversation-history
  - state-management
  - checkpointers
  - context-engineering
  - multi-agent
  - langgraph
  - openai-agents
cluster: agent-design
---

# Agent Memory Architecture

Patterns for managing agent conversation history and long-term memory. This guide explains why manual prompt concatenation fails, how to use state-managed memory correctly, and how to share context between agents.

This document is framework-independent in principles but includes concrete examples for LangGraph and OpenAI Agents SDK.

---

## The Anti-Pattern: Manual Prompt Concatenation

When building agents, developers (and AI coding assistants) often default to manually concatenating conversation history into prompts. This is the most common mistake in agent development.

### What It Looks Like

**Anti-pattern: Naive history concatenation**

```python
# DON'T DO THIS
class NaiveAgent:
    def __init__(self, model):
        self.model = model
        self.history = []  # Manual history list

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        # Stuffing full history into every call
        response = self.model.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *self.history  # Growing unboundedly
            ]
        )

        self.history.append({"role": "assistant", "content": response})
        return response
```

**Problems:**

1. **No persistence**: History lost on restart
2. **Unbounded growth**: Eventually exceeds context window
3. **No thread isolation**: Can't run multiple conversations
4. **Attention degradation**: Middle content gets ignored
5. **Token waste**: Paying for stale context every call

**Anti-pattern: String concatenation**

```python
# DON'T DO THIS
def build_prompt(history: list[dict], new_message: str) -> str:
    history_text = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in history
    ])

    return f"""Previous conversation:
{history_text}

User: {new_message}
Assistant:"""
```

**Problems:**

1. **Format fragility**: Role formatting can confuse the model
2. **No structure**: Loses message boundaries
3. **Injection risk**: History content can break prompt structure
4. **No tool call preservation**: Loses function call context

### Why AI Coding Assistants Default to This

Training data contains many examples of this pattern because:

- It's the simplest implementation
- It works for demos and tutorials
- Framework-specific patterns require API knowledge
- Most code examples don't show production patterns

This is why you have to repeatedly explain you want proper memory management.

### Why It Fails: The Evidence

**"Lost in the Middle" Research (Liu et al., 2023)**

LLMs exhibit a U-shaped attention curve—content at the start and end of context receives attention, middle content is systematically ignored. Stuffing history into the middle of a prompt means important context gets lost.

**The 75% Rule (Claude Code, Anthropic)**

When Claude Code operated above 90% context utilization, output quality degraded significantly. Implementing auto-compaction at 75% produced dramatic quality improvements. The lesson: **capacity ≠ capability**. Empty headroom enables reasoning, not just retrieval.

**Context Rot**

Old, irrelevant details don't just waste tokens—they actively confuse the model. A discussion about error handling from 50 turns ago can distract from the current task, even if technically within the context window.

---

## The Correct Model: State-Managed Memory

Memory should be **first-class state**, not prompt injection. The framework handles storage, retrieval, trimming, and injection—your code focuses on logic.

### Core Principles

**1. Separation of Concerns**

| Concern | Responsibility | Your Code |
|---------|----------------|-----------|
| Storage | Persist messages to durable store | Configure checkpointer |
| Retrieval | Load relevant history for thread | Provide thread_id |
| Trimming | Keep context within limits | Set thresholds |
| Injection | Add history to model calls | Automatic |

**2. Thread Isolation**

Each conversation gets a unique `thread_id`. The framework maintains separate history per thread, enabling concurrent conversations without interference.

**3. Resumability**

Conversations can be paused and resumed—even across process restarts. The checkpointer persists state to durable storage.

**4. Automatic Management**

You don't manually append messages or manage context length. The framework handles this based on configuration.

### LangGraph: Checkpointer Pattern

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, MessagesState

# Development: in-memory
checkpointer = InMemorySaver()

# Production: persistent storage
# checkpointer = SqliteSaver.from_conn_string("conversations.db")

# Define your graph
builder = StateGraph(MessagesState)
builder.add_node("agent", call_model)
builder.add_edge("__start__", "agent")

# Compile WITH checkpointer
graph = builder.compile(checkpointer=checkpointer)

# Each conversation gets a thread_id
config = {"configurable": {"thread_id": "user-123-session-1"}}

# Framework handles history automatically
response = graph.invoke(
    {"messages": [{"role": "user", "content": "Hello!"}]},
    config
)

# Same thread_id = conversation continues
response = graph.invoke(
    {"messages": [{"role": "user", "content": "What did I just say?"}]},
    config  # Same config = same thread
)
```

**What the framework does:**

1. Before invoke: Loads existing messages for thread_id
2. Prepends history to new messages
3. Calls model with full context
4. After invoke: Persists new messages to checkpointer
5. Handles context limits based on configuration

### OpenAI Agents SDK: Session Pattern

```python
from agents import Agent, Runner
from agents.sessions import SQLiteSession

# Create persistent session storage
session = SQLiteSession("conversations.db")

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4o"
)

runner = Runner()

# Session handles history automatically
response = await runner.run(
    agent,
    "Hello!",
    session=session,
    session_id="user-123-session-1"
)

# Same session_id = conversation continues
response = await runner.run(
    agent,
    "What did I just say?",
    session=session,
    session_id="user-123-session-1"
)
```

**What the session does:**

1. Before run: Retrieves conversation history for session_id
2. Prepends history to input items
3. Executes agent with full context
4. After run: Stores new items (user input, responses, tool calls)
5. Handles continuity across runs

---

## Memory Types

Agent memory isn't monolithic. Different types serve different purposes and have different scopes.

### Short-Term Memory (Thread-Scoped)

**Scope**: Single conversation thread
**Purpose**: Maintain context within an ongoing session
**Lifetime**: Duration of conversation (or until explicitly cleared)

| Framework | Implementation |
|-----------|----------------|
| LangGraph | Checkpointer with `thread_id` |
| OpenAI SDK | Session with `session_id` |
| General | Thread-isolated message store |

**What belongs in short-term memory:**

- User messages and assistant responses
- Tool calls and results
- Reasoning traces (if using chain-of-thought)
- Current task state

### Long-Term Memory (Cross-Session)

**Scope**: Across multiple conversations
**Purpose**: Persist facts, preferences, learned patterns
**Lifetime**: Indefinite (or until explicitly deleted)

#### Structured Long-Term Memory

Facts, relationships, and decisions stored in queryable format.

```python
# LangGraph Store pattern
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Store user preference (persists across threads)
store.put(
    namespace=("users", "user-123", "preferences"),
    key="timezone",
    value={"timezone": "America/New_York", "updated": "2025-01-17"}
)

# Retrieve in any thread
prefs = store.get(("users", "user-123", "preferences"), "timezone")
```

#### Semantic Long-Term Memory

Embedding-based retrieval for finding relevant past context.

```python
# Conceptual pattern (framework-independent)
from your_vector_store import VectorStore

memory_store = VectorStore()

# Store interaction summary with embedding
memory_store.add(
    text="User prefers concise responses without code comments",
    metadata={"user_id": "user-123", "type": "preference"},
    embedding=embed("User prefers concise responses...")
)

# Retrieve relevant memories for new context
relevant = memory_store.search(
    query="How should I format code for this user?",
    filter={"user_id": "user-123"}
)
```

### Episodic Memory

**Scope**: Cross-session, timestamped
**Purpose**: Record past interactions for learning and audit
**Lifetime**: Configurable retention

```python
# Record interaction outcome
episodic_store.add({
    "timestamp": "2025-01-17T10:30:00Z",
    "user_id": "user-123",
    "thread_id": "session-456",
    "task": "debug authentication error",
    "outcome": "resolved",
    "approach": "checked token expiration, found clock skew",
    "user_feedback": "positive"
})

# Query past approaches for similar tasks
past_successes = episodic_store.query(
    task_type="debug authentication",
    outcome="resolved",
    user_id="user-123"
)
```

### Memory Layers Summary

| Layer | Scope | Storage | Retrieval | Example Use |
|-------|-------|---------|-----------|-------------|
| Short-term | Thread | Checkpointer/Session | By thread_id | Conversation context |
| Long-term (Structured) | User/Global | Key-value store | By namespace + key | User preferences |
| Long-term (Semantic) | User/Global | Vector store | By similarity | Relevant past context |
| Episodic | User/Global | Event log | By query + time | Past task outcomes |

---

## State-Over-History Principle

A key insight for efficient memory management: **prefer passing current state over full history**.

### The Problem with Full History

```python
# Anti-pattern: Passing full transcript to sub-agent
sub_agent_prompt = f"""
Here's the full conversation so far:
{format_messages(all_300_messages)}

Now help with: {current_task}
"""
```

**Problems:**

- Token explosion
- Attention dilution
- Irrelevant context pollution
- Latency increase

### State-Over-History Pattern

```python
# Better: Pass current state, not history
current_state = {
    "user_goal": "Build a REST API for user management",
    "completed_steps": ["schema design", "database setup"],
    "current_step": "implement CRUD endpoints",
    "decisions_made": {
        "database": "PostgreSQL",
        "framework": "FastAPI",
        "auth": "JWT tokens"
    },
    "open_questions": [],
    "artifacts": ["schema.sql", "models.py"]
}

sub_agent_prompt = f"""
Current project state:
{json.dumps(current_state, indent=2)}

Task: {current_task}
"""
```

**Benefits:**

- Minimal tokens
- Focused attention
- No stale context
- Faster inference

### What Belongs in State vs History

| State (Pass Forward) | History (Store, Don't Pass) |
|---------------------|------------------------------|
| Current goal | How goal was established |
| Decisions made | Discussion leading to decisions |
| Artifacts created | Iterations and revisions |
| Open questions | Resolved questions |
| Error context (if debugging) | Successful operations |

### Implementing State Extraction

```python
# LangGraph: Custom state schema
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class ProjectState(TypedDict):
    messages: Annotated[list, add_messages]  # Short-term (auto-managed)

    # Extracted state (you manage)
    current_goal: str
    decisions: dict
    artifacts: list[str]
    phase: str

# Update state after significant events
def extract_state(messages: list, current_state: ProjectState) -> ProjectState:
    """Extract/update state from recent messages."""
    # Use LLM or rules to identify:
    # - New decisions made
    # - Artifacts created
    # - Phase transitions
    return updated_state
```

---

## Managing History Growth

Even with proper memory architecture, history grows. You need strategies to keep it bounded.

### Strategy 1: Trimming

Keep only the last N turns, drop the rest.

**LangGraph: trim_messages**

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import trim_messages

def trim_to_recent(messages: list) -> list:
    """Keep system message + last 10 messages."""
    return trim_messages(
        messages,
        max_tokens=4000,
        strategy="last",
        token_counter=len,  # Or use tiktoken
        include_system=True,
        allow_partial=False
    )

# Apply before model call
agent = create_react_agent(
    model,
    tools,
    state_modifier=trim_to_recent
)
```

**When to use trimming:**

- Short, transactional conversations
- Tasks where old context is truly irrelevant
- When latency is critical

**Anti-patterns with trimming:**

- Losing critical decisions from early in conversation
- Trimming mid-tool-call (orphaned tool results)
- Using for planning tasks that need long-range context

### Strategy 2: Summarization

Compress older messages into a synthetic summary.

**LangGraph: SummarizationMiddleware**

```python
from langchain.agents import create_agent, SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=tools,
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",  # Cheaper model for summarization
            trigger={"tokens": 4000},  # Trigger when context exceeds
            keep={"messages": 10}  # Keep last 10 verbatim
        )
    ]
)
```

**What summarization produces:**

```
[Summary of turns 1-50]:
- User requested help building a REST API
- Decided on FastAPI + PostgreSQL
- Completed: schema design, database models
- Current focus: authentication implementation
- User prefers concise code without excessive comments

[Recent messages 51-60 kept verbatim]
```

**When to use summarization:**

- Long-running planning conversations
- Support threads spanning multiple issues
- Tasks requiring long-range continuity

**Anti-patterns with summarization:**

- **Summary drift**: Facts get reinterpreted incorrectly
- **Context poisoning**: Errors in summary propagate indefinitely
- **Over-compression**: Losing critical details
- **Summarizing too frequently**: Latency overhead

### Strategy 3: Hybrid (Recommended)

Combine summarization for old context + trimming for recent.

```python
class HybridMemoryConfig:
    # Summarize when total exceeds this
    summarize_threshold_tokens: int = 8000

    # Keep this many recent messages verbatim
    keep_recent_messages: int = 20

    # Maximum summary length
    max_summary_tokens: int = 500

    # Model for summarization (use cheaper model)
    summary_model: str = "gpt-4o-mini"
```

**Flow:**

1. Check total token count
2. If under threshold: no action
3. If over threshold:
   - Keep last N messages verbatim
   - Summarize older messages
   - Replace older messages with summary
   - Continue with bounded context

---

## Multi-Agent Memory Sharing

When multiple agents collaborate, memory sharing becomes critical.

### Pattern 1: Shared State Object

Agents read from and write to a common state.

```python
# LangGraph: Shared state across nodes
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, add_messages

class SharedState(TypedDict):
    messages: Annotated[list, add_messages]

    # Shared across all agents
    research_findings: list[str]
    draft_content: str
    review_feedback: list[str]
    final_output: str

def researcher(state: SharedState) -> SharedState:
    """Research agent adds findings to shared state."""
    findings = do_research(state["messages"][-1])
    return {"research_findings": state["research_findings"] + findings}

def writer(state: SharedState) -> SharedState:
    """Writer agent reads research, produces draft."""
    draft = write_draft(state["research_findings"])
    return {"draft_content": draft}

def reviewer(state: SharedState) -> SharedState:
    """Reviewer reads draft, adds feedback."""
    feedback = review(state["draft_content"])
    return {"review_feedback": feedback}

# Wire agents together
graph = StateGraph(SharedState)
graph.add_node("researcher", researcher)
graph.add_node("writer", writer)
graph.add_node("reviewer", reviewer)
```

### Pattern 2: Artifact Passing (Not Transcript Passing)

**Anti-pattern: Context telephone**

```python
# DON'T DO THIS
def orchestrator_delegates_to_specialist(conversation_history):
    # Passing full history degrades information
    specialist_result = specialist.run(
        f"Here's the conversation:\n{conversation_history}\n\nDo task X"
    )
    return specialist_result
```

**Problems:**

- Information degrades through each handoff
- Irrelevant context pollutes specialist focus
- Token waste compounds at each level

**Better: Pass artifacts and state**

```python
# DO THIS
def orchestrator_delegates_to_specialist(task_state):
    # Pass only what specialist needs
    specialist_result = specialist.run(
        task_description=task_state["current_task"],
        input_artifacts=task_state["relevant_artifacts"],
        constraints=task_state["constraints"],
        # NOT the full conversation history
    )
    return specialist_result
```

### Pattern 3: Memory Isolation vs Sharing

| Scenario | Memory Strategy |
|----------|-----------------|
| Agents working on same task | Shared state object |
| Agents with different domains | Isolated memory, share artifacts |
| Parallel independent tasks | Fully isolated threads |
| Validator reviewing creator's work | Read-only access to creator's output |

**LangGraph: Isolated sub-agents**

```python
# Each specialist gets its own thread
def delegate_to_specialist(state, specialist_graph, task):
    # Create isolated thread for specialist
    specialist_thread_id = f"{state['thread_id']}-{specialist_graph.name}-{uuid4()}"

    result = specialist_graph.invoke(
        {"messages": [{"role": "user", "content": task}]},
        {"configurable": {"thread_id": specialist_thread_id}}
    )

    # Return only the result, not specialist's internal history
    return result["final_output"]
```

### Pattern 4: Namespace-Based Sharing

For long-term memory that should be shared across agents:

```python
# Shared user preferences (all agents can read)
user_namespace = ("users", user_id, "preferences")

# Agent-specific learned patterns (isolated)
agent_namespace = ("agents", agent_id, "patterns")

# Project-specific context (shared within project)
project_namespace = ("projects", project_id, "context")
```

---

## The 75% Rule

Never fill context to capacity. Reserve headroom for reasoning.

### Why Headroom Matters

| Context Usage | Effect |
|---------------|--------|
| < 50% | Optimal reasoning space |
| 50-75% | Good balance |
| 75-90% | Degraded quality, trigger compaction |
| > 90% | Significant quality loss |

### Implementation

```python
def should_compact(messages: list, model_context_limit: int) -> bool:
    """Check if context needs compaction."""
    current_tokens = count_tokens(messages)
    threshold = model_context_limit * 0.75
    return current_tokens > threshold

def auto_compact_middleware(state: AgentState) -> AgentState:
    """Middleware that triggers compaction at 75%."""
    if should_compact(state["messages"], MODEL_CONTEXT_LIMIT):
        state["messages"] = summarize_and_trim(state["messages"])
    return state
```

---

## Implementation Checklist

When building agents, verify:

- [ ] **No manual history concatenation** in prompt building
- [ ] **Checkpointer/Session configured** for conversation persistence
- [ ] **Thread IDs assigned** for conversation isolation
- [ ] **Trimming or summarization** configured for long conversations
- [ ] **State-over-history** for sub-agent delegation
- [ ] **Artifacts passed**, not transcripts, between agents
- [ ] **75% threshold** for context compaction
- [ ] **Long-term memory** separated from short-term (if needed)

---

## Quick Reference

### Pattern Selection

| Situation | Pattern | Framework Feature |
|-----------|---------|-------------------|
| Basic conversation persistence | Checkpointer/Session | LangGraph: `InMemorySaver`, OpenAI: `SQLiteSession` |
| Long conversations | Summarization middleware | LangGraph: `SummarizationMiddleware` |
| Multi-agent shared context | Shared state schema | LangGraph: `StateGraph` with shared `TypedDict` |
| Cross-session user data | Long-term store | LangGraph: `InMemoryStore`, MongoDB Store |
| Semantic memory retrieval | Vector store integration | External: Pinecone, Chroma, pgvector |

### Anti-Pattern Recognition

| If you see... | It's wrong because... | Replace with... |
|---------------|----------------------|-----------------|
| `history.append(msg)` | Manual management | Checkpointer |
| `prompt += history` | String concatenation | Session with auto-injection |
| Full transcript to sub-agent | Context telephone | Artifact/state passing |
| No thread_id | No isolation | Explicit thread management |
| No trimming/summarization | Unbounded growth | Memory middleware |

---

## Research Basis

| Source | Key Finding |
|--------|-------------|
| "Lost in the Middle" (Liu et al., 2023) | U-shaped attention; middle content ignored |
| Claude Code 75% Rule (Anthropic) | Quality degrades above 75% context usage |
| LangChain Short-Term Memory Guide | Checkpointer + summarization patterns |
| OpenAI Agents SDK Session Docs | Session-based auto-persistence |
| AWS Memory-Augmented Agents | Memory layer architecture patterns |
| A-Mem (2025) | Dynamic vs predefined memory access |

---

## See Also

- [Agent Prompt Engineering](agent_prompt_engineering.md) — Context architecture, active pruning, state-over-history principle
- [Multi-Agent Patterns](multi_agent_patterns.md) — Delegation, context passing, artifact handoffs
