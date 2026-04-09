# Simple Model Evals

Copy-paste these into the CLI to compare model behavior. Each prompt is self-contained.

---

## Tool Use Accuracy

```max_loops=5
Find all Python files under src/tools/ that contain the word "async" and tell me how many there are.
```

```max_loops=3
Read the file context/identity.md and summarize it in one sentence.
```

```max_loops=3
What is the current working directory? List all top-level folders.
```

---

## Multi-Step Planning

```max_loops=15
I want to add a new tool called "summarize" that takes a file path and returns a summary. Walk me through every file I'd need to change and in what order, but don't make any changes.
```

```max_loops=15
Find every skill that uses the "attach" tool, then for each one tell me what it does and why it needs attach.
```

```max_loops=20
Figure out how an incoming message travels from the WebSocket connection all the way to a tool being executed. Trace the full path through the code, citing files and line numbers.
```

---

## Memory Retrieval

```max_loops=8
What do you know about me? Check your memory before answering.
```

```max_loops=5
Before answering this: what projects am I currently working on? Look in memory first.
```

```max_loops=10
Who are the people you remember? Check context/memory/ for any information about contacts or collaborators.
```

---

## Instruction Following

```max_loops=8
What is your name and what are you? Answer only from your identity file, don't make anything up.
```

```max_loops=2
List all skills you have available. Only list what's in your skill manifest, nothing else.
```

```max_loops=1
I want you to write a haiku about the ocean. Do not use any tools — just respond directly.
```

---

## Skill Orchestration

```max_loops=12
Load the web-search skill and search for "asyncio best practices 2025". Summarize the top results.
```

```max_loops=5
Load the deep-research skill and tell me what sub-skills it depends on before running anything.
```

```max_loops=5
Which skill would you use to research a topic on Reddit? Load it and explain what it does.
```

---

## Error Recovery

```max_loops=3
Read the file src/nonexistent/fake_module.py and tell me what's in it.
```

```max_loops=3
Run the bash command `python -c "import nonexistent_module"` and handle whatever happens.
```

```max_loops=3
Search for the pattern "zzz_no_match_zzz" across the entire codebase. What do you conclude?
```

---

## Output Quality

```max_loops=8
Explain how Curunir's context overflow handling works. Be concise — under 100 words.
```

```max_loops=5
Compare the delegate tool to a simple function call. When would you use one vs the other?
```

```max_loops=10
Read src/agent/agent.py, src/tools/dispatcher.py, and src/skills.py. What is the most important design decision in each file? Justify briefly.
```

---

## Efficiency

```max_loops=8
What model am I configured to use? Find the answer with as few tool calls as possible.
```

```max_loops=3
Does this project have any scheduled tasks? Check and report.
```

```max_loops=8
How many tests does this project have? Just give me the number.
```
