# pydynamix

> **A powerful dynamic execution and code manipulation library.**

This module provides advanced tools for dynamic code execution, variable management,
and metaprogramming capabilities in Python. It enables secret variable storage,
dynamic execution with result capture, scope manipulation, lambda creation, and
class extension.

Key Features:
- Secret variable storage and retrieval (`setvar`, `getvar`, `delvar`, `clearvars`)
- Dynamic code execution with results (`resulted_execution`)
- Scope context management (`scope_context`)
- Anonymous function generation (`GreatLambda`)
- Class extension and composition (`extend`)
- Module export control (`export`)
- Custom object construction decorator (`constructor`)

Classes:

**ReadOnly**: Contains nested type-only classes for typing purposes.
    - **ExecutionResults**: Represents results from dynamic code execution.
    - **Scoper**: Provides scope attribute access and management.
    - **ScopeContext**: Context manager for scope attribute revelation.

**GreatLambda**: Builder for creating advanced anonymous functions.

**constructor**: Decorator for constructing objects via function definitions.

Functions:
- `setvar`: Store a variable secretly.
- `getvar`: Retrieve a secretly stored variable with optional default.
- `delvar`: Delete a specific secret variable by name.
- `clearvars`: Clear all secret variables.
- `takevar`: Retrieve a secret variable or raise `KeyError` if not found.
- `resulted_execution`: Execute code dynamically and capture execution results.
- `extend`: Extend a class with attributes from another class.
- `scope_context`: Create a context manager for accessing object attributes.
- `export`: Define which variables a module should export.