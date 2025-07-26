# DSCommon Code Analysis

This document summarizes the source code structure and key components of the `AZ_DSCommon` project from GitHub.

## Overview

The project is a Play Framework module that implements a document flow and rights management library. It provides models, controllers, and utilities for creating, updating, and managing document-based workflows. The code is primarily written in Java with supporting configuration in YAML and Play Framework files.

## Repository Structure

Main folders under the `app` directory include:

- `code/docflow` – core library containing document models, compiler classes, queries, and utilities.
- `controllers` – HTTP controllers exposing CRUD and file endpoints.
- `models` – generated document entities such as `BuiltInUser` and `DocflowFile`.
- `ngapp` – client-side Angular code generation templates.

Configuration files live in the `conf` directory and define routes, messages, and Play settings.

## Key Components

### Docflow API

The `Docflow` class exposes high-level operations such as document creation, update, and deletion. The following snippet illustrates the creation workflow:

```java
public static <T extends DocumentPersistent> T create(final DocType docType, final ObjectNode update, final Result result) {
    if (!DocflowJob.isWithinScope() || Transaction.instance().isWithinScope()) {
        final Result localResult = new Result();
        T res = (T) DocflowApiCreate._create(docType, null, update, null, null, localResult);
        result.append(localResult);
        return res;
    } else
        return Transaction.scope(result, new Transaction.Delegate<T>() {
            @Override
            public T body(int attempt, Result result) {
                T res = (T) DocflowApiCreate._create(docType, null, update, null, null, result);
                return res;
            }
        });
}
```

### Generated Models

Models are generated at build time. For example, `DocflowFile` represents a file entity with states and actions:

```java
@Entity(name = "doc_docflow_file")
public class DocflowFile extends DocumentSimple {
    public static final String TABLE = "doc_docflow_file";
    @Id
    @SequenceGenerator(name = "doc_docflow_file_seq", sequenceName = "doc_docflow_file_seq", initialValue = 1, allocationSize = 1)
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "doc_docflow_file_seq")
    public long id;
    @Transient
    public String text = "";
    @Column(length = 100, nullable = false, columnDefinition = "character varying(100) default ''")
    public String filename = "";
    // ...
}
```

### Configuration Loading

Compilation steps load YAML definitions and link them to code. For instance, `Compiler030LoadFieldTypes` reads field type definitions from module directories:

```java
public class Compiler030LoadFieldTypes {
    public static void doJob(DocflowConfig docflowConfig, Result result) {
        final Result localResult = new Result();
        for (int i = docflowConfig.modules.length - 1; i >= 0; i--) {
            docflowConfig.currentModule = docflowConfig.modules[i];
            final VirtualFile file = docflowConfig.currentModule.root.child(DocflowConfig.PATH_FIELD_TYPES);
            if (!file.exists())
                continue;
            // parsing YAML and merging field types
        }
    }
}
```

## Conclusion

`AZ_DSCommon` provides a comprehensive framework for document management in Play applications. It includes a dynamic compiler for YAML-defined documents, generated models with state machines, and HTTP endpoints for file and document operations.
