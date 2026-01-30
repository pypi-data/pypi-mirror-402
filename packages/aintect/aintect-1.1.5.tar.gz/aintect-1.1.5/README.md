# Generate source and wheel distribution
python -m build

# Install wheel file
pip install dist/aintect-1.0.0-py3-none-any.whl

# Publish to Pypi
python -m twine upload dist/*