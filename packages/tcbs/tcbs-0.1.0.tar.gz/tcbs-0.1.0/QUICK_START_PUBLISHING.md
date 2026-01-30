# Quick Start: Publishing TCBS to PyPI

## ⚠️ Pre-Flight Checklist

Before publishing, ensure:

1. **Remove sensitive files** (they're in .gitignore but shouldn't exist):
   ```bash
   rm .key test_api_key.py Untitled.ipynb
   ```

2. **Validate package**:
   ```bash
   python3 check_package.py
   ```
   Should show: ✅ Package is ready for publishing!

3. **Test imports locally**:
   ```bash
   python3 -c "from tcbs import TCBSClient; print('OK')"
   ```

## 🚀 Publishing Steps

### 1. Install Build Tools
```bash
pip3 install --upgrade build twine
```

### 2. Clean and Build
```bash
rm -rf build/ dist/ *.egg-info/
python3 -m build
```

This creates:
- `dist/tcbs-0.1.0-py3-none-any.whl`
- `dist/tcbs-0.1.0.tar.gz`

### 3. Test on Test PyPI (Recommended First Time)
```bash
python3 -m twine upload --repository testpypi dist/*
```

Enter your Test PyPI credentials when prompted.

Test installation:
```bash
pip3 install --index-url https://test.pypi.org/simple/ --no-deps tcbs
python3 -c "import tcbs; print(tcbs.__version__)"
```

### 4. Publish to Production PyPI
```bash
python3 -m twine upload dist/*
```

Enter your PyPI credentials when prompted.

### 5. Verify Installation
```bash
pip3 install tcbs
python3 -c "import tcbs; print(tcbs.__version__)"
```

### 6. Tag Release
```bash
git add .
git commit -m "Release v0.1.0"
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin main
git push origin v0.1.0
```

## 🔑 Using API Tokens (Recommended)

Instead of username/password:

1. Generate token at https://pypi.org/manage/account/token/
2. When prompted:
   - Username: `__token__`
   - Password: `pypi-...` (your token)

## 📝 For Future Releases

1. Update version in `tcbs/__init__.py`
2. Update `CHANGELOG.md`
3. Run `python3 check_package.py`
4. Follow steps 2-6 above

## ❓ Troubleshooting

**"Package already exists"**
- Version 0.1.0 is already published
- Increment version in `tcbs/__init__.py` (e.g., 0.1.1)

**"403 Forbidden"**
- Package name might be taken
- Check https://pypi.org/project/tcbs/

**"Invalid credentials"**
- Verify PyPI account
- Use API token instead of password

**"File not found"**
- Run `python3 -m build` first
- Check `dist/` directory exists

## 📦 What Gets Published

Only these files are included in the PyPI package:
- `tcbs/` directory (all .py files)
- `README.md`
- `LICENSE`
- `requirements.txt`

Excluded (via MANIFEST.in):
- `.key`, `*.key`
- `example.py`, `test_api_key.py`
- `*.ipynb`
- `openapi.json`
- `__pycache__/`, `*.pyc`

## ✅ Success Indicators

After publishing, you should be able to:
1. Visit https://pypi.org/project/tcbs/
2. Install with `pip install tcbs`
3. Import with `from tcbs import TCBSClient`
4. See your README on the PyPI page
