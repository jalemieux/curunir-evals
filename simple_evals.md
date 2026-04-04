# Simple Model Evals

Copy-paste these into the CLI to compare model behavior. Each prompt is self-contained.

---

## Tool Use Accuracy

```
Find all Python files under src/tools/ that contain the word "async" and tell me how many there are.
```

```
Read the file context/identity.md and summarize it in one sentence.
```

```
What is the current working directory? List all top-level folders.
```

---

## Multi-Step Planning

```
I want to add a new tool called "summarize" that takes a file path and returns a summary. Walk me through every file I'd need to change and in what order, but don't make any changes.
```

```
Find every skill that uses the "attach" tool, then for each one tell me what it does and why it needs attach.
```

```
Figure out how an incoming message travels from the WebSocket connection all the way to a tool being executed. Trace the full path through the code, citing files and line numbers.
```

---

## Memory Retrieval

```
What do you know about me? Check your memory before answering.
```

```
Before answering this: what projects am I currently working on? Look in memory first.
```

```
Who are the people you remember? Check context/memory/ for any information about contacts or collaborators.
```

---

## Instruction Following

```
What is your name and what are you? Answer only from your identity file, don't make anything up.
```

```
List all skills you have available. Only list what's in your skill manifest, nothing else.
```

```
I want you to write a haiku about the ocean. Do not use any tools — just respond directly.
```

---

## Skill Orchestration

```
Load the web-search skill and search for "asyncio best practices 2025". Summarize the top results.
```

```
Load the deep-research skill and tell me what sub-skills it depends on before running anything.
```

```
I want to research what people on Reddit think about LLM eval frameworks. Use the appropriate skill.
```

---

## Error Recovery

```
Read the file src/nonexistent/fake_module.py and tell me what's in it.
```

```
Run the bash command `python -c "import nonexistent_module"` and handle whatever happens.
```

```
Search for the pattern "zzz_no_match_zzz" across the entire codebase. What do you conclude?
```

---

## Output Quality

```
Explain how Curunir's context overflow handling works. Be concise — under 100 words.
```

```
Compare the delegate tool to a simple function call. When would you use one vs the other?
```

```
What are the three most important design decisions in this codebase? Justify each briefly.
```

---

## Efficiency

```
What model am I configured to use? Find the answer with as few tool calls as possible.
```

```
Does this project have any scheduled tasks? Check and report.
```

```
How many tests does this project have? Just give me the number.
```
