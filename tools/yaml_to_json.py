import json
import sys

try:
    import yaml
except ImportError:
    print("PyYAML is required")
    sys.exit(1)


def yaml_to_json(in_path, out_path=None):
    with open(in_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python yaml_to_json.py <input.yml> [output.json]")
        sys.exit(1)
    yaml_to_json(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
