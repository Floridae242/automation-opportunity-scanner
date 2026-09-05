from pathlib import Path
import json
try:
    import yaml
except Exception:
    yaml = None

root = Path(__file__).resolve().parents[1]
errors = []
for p in root.rglob('*.json'):
    try:
        json.loads(p.read_text())
    except Exception as e:
        errors.append(f"JSON {p.relative_to(root)}: {e}")
if yaml:
    for p in list(root.rglob('*.yaml')) + list(root.rglob('*.yml')):
        try:
            yaml.safe_load(p.read_text())
        except Exception as e:
            errors.append(f"YAML {p.relative_to(root)}: {e}")
required = [
    'MASTER_INSTRUCTIONS.md','AI_BUILD_MANIFEST.yaml','docs/requirements/SRS.md',
    'docs/domain/OPPORTUNITY_SCORING_MODEL.md','docs/architecture/SYSTEM_ARCHITECTURE.md',
    'docs/data/DATABASE_SCHEMA.md','docs/api/OPENAPI.yaml','docs/testing/DEFINITION_OF_DONE.md'
]
for r in required:
    if not (root/r).exists(): errors.append(f"Missing required file: {r}")
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
print('Pack validation OK')
