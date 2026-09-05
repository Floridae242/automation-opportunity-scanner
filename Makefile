.PHONY: validate docs
validate:
	python scripts/validate_pack.py

docs:
	@echo "Read README.md -> MASTER_INSTRUCTIONS.md -> AI_BUILD_MANIFEST.yaml"
