## Publishing Process

Increment the version number as appropriate in pyproject.toml. Delete old
builds from dist/. Run uv sync to update the lock file. Commit the changes,
which should have just changes to pyproject.taml and uv.lock. 