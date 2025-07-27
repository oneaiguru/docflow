# Docflow Documentation Repository

This repository contains analysis and documentation for the original **AZ_DSCommon** project.

Configuration examples are now provided in **JSON v2** instead of YAML. A helper script under `tools/yaml_to_json.py` demonstrates how to convert legacy YAML files to JSON format.

## Python Docflow Example

This repository now includes a simplified Python reimplementation of the key
ideas from **AZ_DSCommon**. The code can be found in the `py_docflow` package.
It demonstrates how document types, documents and basic actions can be managed
without the Play Framework. Recent additions include rudimentary history storage
for versioned documents, a sample action that links documents together, and
simple role based rights checks protecting create, update, delete and other
actions.

To try the demo:

```bash
python -m py_docflow_demo
```
The script creates two documents as an admin user, links them together and shows
how role based rights prevent a guest from deleting records.
