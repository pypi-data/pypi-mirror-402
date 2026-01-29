# PyPI Trusted Publishing Setup Guide

## Step-by-Step Instructions

### Step 1: Configure PyPI Trusted Publisher

1. **Go to PyPI Publishing Settings**
   - URL: https://pypi.org/manage/account/publishing/
   - Log in with your PyPI account (same one used for prlyn)

2. **Add New Trusted Publisher**
   - Look for section: **"Add a new trusted publisher"** or **"Pending publishers"**
   - Click **"Add"** or **"Create"** button

3. **Fill in the Form**
   ```
   Publisher name: sef-agents (or any descriptive name)
   Provider: GitHub
   Owner: Mishtert
   Repository name: sef-agents
   Workflow filename: .github/workflows/publish.yml
   Environment name: pypi (optional but recommended)
   ```

4. **Save**
   - Click **"Add"** or **"Create"** to save

### Step 2: Create GitHub Environment (Optional but Recommended)

1. **Go to GitHub Repository Settings**
   - URL: https://github.com/Mishtert/sef-agents/settings/environments
   - Or: Repo → Settings → Environments (left sidebar)

2. **Create New Environment**
   - Click **"New environment"** button
   - Name: `pypi`
   - Click **"Configure environment"**

3. **Save**
   - No secrets needed (trusted publishing uses OIDC)
   - Click **"Save protection rules"**

### Step 3: Verify Setup

After setup, when you push a version tag:
```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will automatically:
- Build the package
- Validate metadata
- Publish to PyPI

Check workflow run: https://github.com/Mishtert/sef-agents/actions

## Visual Guide

**PyPI Page Location:**
```
PyPI Dashboard → Account Settings → Publishing → Add trusted publisher
```

**GitHub Page Location:**
```
Repository → Settings → Environments → New environment
```

## Troubleshooting

**If publisher already exists for prlyn:**
- You can reuse the same PyPI account
- Just add a NEW trusted publisher for `sef-agents` repository
- Each repository needs its own trusted publisher entry

**If environment creation fails:**
- Environment name is optional
- Workflow will still work without it
- But it's recommended for security

## Next Steps

After setup is complete:
1. Update version in `pyproject.toml` if needed
2. Commit and push changes
3. Create version tag: `git tag v0.1.0 && git push origin v0.1.0`
4. Watch GitHub Actions publish automatically
