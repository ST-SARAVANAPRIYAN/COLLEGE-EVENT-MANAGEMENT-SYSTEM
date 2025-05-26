# GitHub Copilot Instruction File

## Core Coding Requirements

- Implement enhanced and structured exception handling using specific exception types and clear control flow (`try/except/else/finally`).
- Automatically check for and create necessary directories before writing or reading files. Ensure proper file placement based on function and purpose.
- Always include concise and meaningful comment lines, particularly when referencing or importing modules, files, or external resources.
- Follow principles of clean code: modular structure, single-responsibility functions, readable naming, and efficient control flow.
- Ensure all code is optimized, reusable, and structured for maintainability and performance across large codebases.

## Interaction Rules

- Before generating or modifying any code, describe the intended changes in detail, including affected files, functions, and the purpose of the change.
- Ask for clarification when assumptions are necessary or when user intent is ambiguous.

## Performance and Scalability

- Maintain small, focused files and functions to reduce token overhead and avoid performance degradation in large projects.
- Avoid generating or proposing large monolithic files. Instead, recommend modular architecture and shared utility components.
- Use descriptive and predictable file and folder naming conventions to aid navigation and maintain consistency.
- Leverage workspace-wide context only when required and avoid redundant repetition of existing logic or definitions.

## Code Quality Standards

- Enforce logical separation of concerns across layers such as database access, business logic, and presentation.
- Use clear and maintainable patterns for file organization, such as grouping by feature or layer (e.g., services/, models/, routes/).
- Minimize code duplication. Abstract shared logic into functions, utilities, or modules.
- Apply security best practices, especially when handling user input, credentials, or system-level operations.
- Follow language-specific formatting and styling conventions (e.g., PEP8 for Python, W3C for HTML/CSS, standard JS style guides).

## Large Project Guidance

- Do not assume full-file context in large files. Instead, rely on modular structure, references, and local scopes.
- Avoid generating code that relies on understanding the full project unless requested or explicitly scoped.
- When context size is a limitation, notify the user and suggest refactoring or narrowing the request scope.
- Suggest creating code indexes or modular summaries to improve Copilot's navigation and response accuracy in large repositories.

## Prompt Behavior

- When context is ambiguous, prompt the user for clarification before proceeding.
- For sensitive operations such as file deletion, data migration, or external API usage, always prompt for explicit approval.

