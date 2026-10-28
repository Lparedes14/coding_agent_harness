---
name: performance
description: Diagnose and improve performance using measurement rather than guesswork.
---

# Performance

Use this skill when code is slow, uses too much memory, or must meet a specific performance target.

## Instructions

Define the metric that matters, such as latency, throughput, memory, or startup time, and the workload used to measure it.

Measure a baseline before changing anything, and record the command and the result.

Profile or trace to find the dominant cost. Do not optimize based on intuition or on code that is not hot.

Look first for algorithmic complexity, repeated I/O, N+1 queries, unnecessary serialization, unbounded growth, and allocations inside loops.

Change one thing at a time and re-measure after each change. Keep the version that actually improves the metric.

Preserve correctness: run the relevant tests after every optimization.

Stop when the target is met or the remaining gains are marginal. Report the baseline, the change, the measured result, and any tradeoffs or limits.
