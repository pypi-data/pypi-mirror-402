# cxppython
### install build
- python -m pip install --upgrade pip setuptools wheel twine
- 
### build
- python setup.py sdist bdist_wheel
### upload
- twine upload dist/*