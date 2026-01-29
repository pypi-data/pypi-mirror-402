# Building and Publishing Toto MS package on Pypi

To build and publish a new version on Pypi follow this guide. 

## Building the package
To **build** the package, first make sure that ´build´ is installed (`pip install build`) and then run: 
```
python -m build
```

## Upload on Pypi
To **upload** the package to PyPi, run:
```
twine upload dist/* 
```

You can change the version in: `pyproject.toml` and `setup.py`.

Notes: 

* Make sure you only have the stuff you want to publish under dist, otherwise you'll get an error stating that the files already exist.

* Note that to **publish** packages to PyPi, you need to authenticate via token. <br>
The token needs to be stored in `$HOME/.pypirc` in this format: 
```
[pypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmcCJDMwZDZlMjYzLWExZWUtNGI0ZC......
```
Note that the "username" value is the string `__token__`. The actual token only goes in the password field.

## Additional information
 * [Notes on starting and configuring a Python Virtual Environment](https://snails-shop-mta.craft.me/fo93w8gh34GEUH)