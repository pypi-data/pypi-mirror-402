# Publishing to PyPI

## Automated Publishing (Recommended)

Uses GitHub Actions with **trusted publishing** (same setup as prlyn). No API tokens needed.

### Setup (One-time)

1. **Configure PyPI Trusted Publishing**:
   - Go to https://pypi.org/manage/account/publishing/
   - Add new trusted publisher
   - Select "GitHub" as provider
   - Repository: `Mishtert/sef-agents`
   - Workflow filename: `.github/workflows/publish.yml`
   - Environment name: `pypi`

2. **Create GitHub Environment** (if not exists):
   - Go to repo Settings → Environments
   - Create `pypi` environment
   - No secrets needed (trusted publishing uses OIDC)

### Publishing Steps

1. **Update version** in `pyproject.toml`:
   ```toml
   [project]
   version = "0.1.0"  # Increment as needed
   ```

2. **Commit and push**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.0"
   git push
   ```

3. **Create version tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. **GitHub Actions automatically**:
   - Builds package
   - Validates version consistency
   - Publishes to PyPI

### Manual Publishing (Fallback)

If trusted publishing isn't configured:

```bash
# 1. Update version in pyproject.toml
# 2. Build
uv build

# 3. Check metadata
uv tool run twine check dist/*

# 4. Publish (requires PyPI credentials)
uv publish
```

### Verify Installation

After publishing:
```bash
uvx sef-agents --help
```

## Post-Publish

Users can now install simply:
```json
{
  "mcpServers": {
    "sef-agents": {
      "command": "uvx",
      "args": ["sef-agents"]
    }
  }
}
```

## Version Management

- **Patch** (0.1.0 → 0.1.1): Bug fixes
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes
