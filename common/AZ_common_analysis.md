# AZ_common Code Analysis

The `AZ_common` repository contains a set of utilities and services used across various projects. It is implemented with Node.js modules organized by feature. Key components include:

- **connectors** – wrappers around external systems such as PostgreSQL, MSSQL, Dgraph and SOAP services. Each connector defines event schemas, service types and related logic.
- **services** – abstractions for starting/stopping services, health checking and node management. Includes event definitions and state management.
- **errors** – common error types with validation schemas for consistent error events and utilities for logging.
- **validation** – a small validation framework that exports `VType` definitions, argument validation helpers and built-in type rules.
- **context & monitoring** – helpers for tracking context identifiers between requests and exposing health counters via HTTP.
- **utils** – various helper utilities (e.g. `ensureDir`, `addPrefixToErrorMessage`, `fixSpaces`) used by other parts of the code base.

The project also contains samples and build helpers demonstrating how the components fit together. Many modules include TypeScript-style validation schemas to enforce strict data structures. Documentation is available throughout the folder tree in Markdown files written mostly in Russian.
