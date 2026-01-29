# Store direct dependencies in a requirements.txt.
uv sync --no-default-groups --no-install-project
uv pip freeze > requirements.txt

# Install all dependencies.
uv sync

# Build the BOM.
uv run cyclonedx-py requirements --pyproject pyproject.toml --mc-type library -o bom.json

# Manually store the version.
# https://github.com/CycloneDX/cyclonedx-python/issues/1013
VERSION=$(uv run hatch version)
< bom.json jq --arg version "$VERSION" '.metadata.component.version = $version' | sponge bom.json

# Cleanup.
rm requirements.txt
