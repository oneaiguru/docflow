# AZ_DSCommon Project Analysis

The [AZ_DSCommon](https://github.com/oneaiguru/AZ_DSCommon) repository provides a set of Play Framework 1.2+ components aimed at simplifying development of document-centric applications. It delivers server side libraries for docflow processing and AngularJS front‑end modules.

## Repository Layout

```
AZ_DSCommon/
├── app/            # Java code and Play templates
│   ├── code/       # Core library classes (Docflow, actions, API)
│   ├── controllers # HTTP API endpoints
│   ├── docflow/    # YAML configuration and localization
│   ├── models/     # Generated document model classes
│   └── views/      # Play views
├── conf/           # Play configuration (routes, dependencies, messages)
├── static/         # Front‑end assets (AngularJS, CSS, etc.)
└── build.coffee    # Gulp build script
```

## Key Functionality

- **Docflow API** – Java classes under `app/code/docflow` implement document creation, update, deletion and action invocation. The `Docflow` class orchestrates database transactions and delegates to `DocflowApi*` helpers.
- **Controllers** – Classes in `app/controllers` expose RESTful routes defined in `conf/routes` such as `/api/list/{docType}` and `/api/action/{id}/{action}` for listing and performing actions on documents.
- **Models** – Document classes like `DocflowFile` extend framework base classes to provide persistence and state management.
- **Front‑end** – The `static/ngApp` directory contains precompiled AngularJS modules (e.g., `dscommon.min.js`) that interact with the server API.

## Configuration

- `conf/application.conf` defines Play settings such as `application.name=DSCommon` and uses port 9010 for local development.
- `conf/dependencies.yml` lists required libraries including Guava and Jackson.
- `conf/messages` stores UI strings in Russian (e.g., `validation.required=Не заполнено`).

## Build Setup

JavaScript and CSS assets are processed via Gulp (`gulpfile.coffee`). The package.json file declares development dependencies such as `gulp` and `coffee-script` for building the front‑end resources.

## License

AZ_DSCommon is distributed under the Apache 2.0 License.

