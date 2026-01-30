# Publishing TCBS to PyPI

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - Test PyPI: https://test.pypi.org/account/register/
   - Production PyPI: https://pypi.org/account/register/

2. **Install Build Tools**:
```bash
pip install --upgrade pip setuptools wheel twine build
```

## Pre-Publication Checklist

- [ ] All tests pass
- [ ] Version updated in `tcbs/__init__.py`
- [ ] CHANGELOG.md updated
- [ ] No API keys in code
- [ ] LICENSE file present

## Build and Publish

### 1. Clean Previous Builds
```bash
rm -rf build/ dist/ *.egg-info/
```

### 2. Build Package
```bash
python -m build
```

### 3. Test on Test PyPI (Recommended)
```bash
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ tcbs
```

### 4. Publish to PyPI
```bash
python -m twine upload dist/*
```

### 5. Create Git Tag
```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## Using API Tokens

Use tokens instead of passwords:
- Generate at https://pypi.org/manage/account/token/
- Username: `__token__`
- Password: Your token (starts with `pypi-`)

## Troubleshooting

- **403 Forbidden**: Check package name availability
- **400 Bad Request**: Verify version number is unique
- **File exists**: Version already published, increment version
