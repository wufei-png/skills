---
name: codex-thread-report
description: Report findings from this chat to an existing Codex thread when the user asks to send them.
disable-model-invocation: true
---

# Codex Thread Report

1. Identify the destination by thread ID, using `list_threads` if needed. Read its recent turns with `read_thread` to confirm the target and its latest context. If it is ambiguous or cannot be read, provide a copyable report here.
2. Summarize the relevant findings from this chat, focusing on what the destination does not already know. Include sources, uncertainty, and a next step when useful.
3. Send once with `send_message_to_thread` only when the user explicitly asks to send to that thread. If the result is uncertain, inspect the destination before retrying.
