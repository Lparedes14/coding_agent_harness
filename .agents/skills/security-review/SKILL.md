---
name: security-review
description: Audit code for exploitable vulnerabilities and report findings without editing files.
---

# Security Review

Use this skill when reviewing authentication, authorization, input handling, data storage, or any code exposed to untrusted input.

## Instructions

Review only; do not edit files.

Map the entry points that accept untrusted data: HTTP handlers, CLI arguments, file uploads, message queues, environment configuration, and third-party responses.

Trace data from each source to its sinks. Check for injection in SQL, shell commands, templates, and logs, plus path traversal, unsafe deserialization, server-side request forgery, and cross-site scripting.

Check access control explicitly: whether every sensitive action verifies identity and authorization, and whether checks fail closed.

Look for secrets in source, configuration, logs, and error messages. Review cryptography, random number generation, session handling, CORS, and cookie settings.

Review dependencies for known-vulnerable or unmaintained packages when a lockfile or audit tool is available.

Report only issues you can justify. For each finding, give severity, file and line, the attack scenario, and a concrete remediation. Separate confirmed problems from hardening suggestions, and state what you could not verify.
