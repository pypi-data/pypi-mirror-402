pip install build twine


rm -rf dist
rm -rf *.egg-info
python -m build

python -m twine upload dist/*

pip install --upgrade dynamic-temporal-models