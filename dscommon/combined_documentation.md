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
# Модель документов и операции DSCommon

Этот файл содержит обзор классов модели документов из Java-репозитория **AZ_DSCommon** и описывает основные операции, реализованные в пакете `code.docflow`.

## Базовые классы моделей

- **Document** – абстрактный базовый класс всех документов. Он определяет методы `_docType()`, `_state()`, `_fullId()` и работу со сменой состояния. В классе предусмотрен метод `calculate` для вычисления вычисляемых полей.
- **DocumentPersistent** – наследуется от `Document` и добавляет метод `_attached()` для повторной загрузки объекта из базы данных.
- **DocumentSimple** – содержит поля `creator` и `created` и устанавливает их перед сохранением документа.
- **DocumentVersioned** – дополняет документ версией `rev`, полями `created`, `modified` и флагом `deleted`.

Пример сгенерированного документа `DocflowFile` можно увидеть в существующем файле анализа. Класс использует перечисления для состояний, фильтров, сортировок и действий и содержит основные поля файла:

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

Источник: `dscommon/analysis.md` строки 48–60.

## Определение типа документа

Типы документов описываются классом `DocType`. Он содержит коллекции полей, групп полей, шаблонов отображения, действий, связей, фильтров и состояний. Также в объекте `DocType` хранится набор масок прав и служебная информация, например `jsonBinder` и методы `textMethod` и `calculateMethod`.

## Основные операции

Работа с документами выполняется через набор классов `DocflowApi*`:

- **Создание** – метод `DocflowApiCreate._create` создаёт новый экземпляр документа, применяет начальные значения и выполняет встроенное действие `CREATE`.
- **Обновление** – `DocflowApiUpdate._update` принимает JSON‑данные, проверяет права и применяет изменения к полям документа. При необходимости вызывается пользовательский метод `preUpdate` и выполняется действие `UPDATE`.
- **Удаление и восстановление** – класс `DocflowApiDelete` изменяет флаг `deleted` у объектов `DocumentVersioned` и вызывает действие `DELETE` или `RECOVER`.
- **Действия** – `DocflowApiAction._action` запускает произвольное действие документа. Внутри проверяются права, состояние документа и выполняются переходы состояний.
- **Файлы** – вспомогательный класс `DocflowApiFile` содержит методы `_persistFile` для сохранения загружаемого файла как `DocflowFile` и `_getFile` для получения физического файла по документу.

Функция верхнего уровня `Docflow.create` отображает общий процесс создания документа. Её часть приведена в `dscommon/analysis.md` строках 27–40:

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

## Контроллеры

HTTP‑контроллеры из пакета `controllers` предоставляют REST‑интерфейс:

- `DocflowHttpListController.list` – вывод списка документов по типу и шаблону.
- `DocflowHttpActionController.action` – универсальная точка для выполнения действий, в том числе создания, обновления и удаления.
- `DocflowHttpFileController` – работа с `DocflowFile` (загрузка и скачивание).

## Итог

Модель документов в AZ_DSCommon построена на основе описаний `DocType` и классов наследования `Document*`. Операции над документами реализованы в `DocflowApiCreate`, `DocflowApiUpdate`, `DocflowApiDelete` и `DocflowApiAction`, а взаимодействие через HTTP обеспечивают контроллеры Play Framework.

