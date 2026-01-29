# singlejson
![GitHub issues](https://img.shields.io/github/issues/IgnyteX-Labs/singlejson) 
![PyPI](https://img.shields.io/pypi/v/singlejson)

A simple set of utilities for working with JSON in Python.

View the [documentation](https://singlejson.readthedocs.io/) here.

## Features:
* Easy loading of JSON files
* One instance for each opened file
* Multiple ways of handling default values

## Installation:
Install singlejson using pip
```shell
pip install singlejson
```

## Usage:
Loading JSON from a file:
```python
import singlejson

file = singlejson.load('file.json')  # Load file.json
# Returns a JSONFile object which has the json property
file.json["fun"] = True  # Edit some values in the JSONFile
```
When we load the same file from the filesystem again, we get the same object:
```text
import singlejson
file2 = singlejson.load('file.json')
print(file2.json["fun"])  # > True
```

To save the file back to the disk we call ``file.save()``

If the requested file doesn't exist, the file and its parent directories
will be created and *default_data* will be written.
```text
import singlejson
file = singlejson.load('new_file.json', default_data={"fun": False})
print(file.json)  # > {"fun": False}
```

Or initialize the file with a default file path:
```text
import singlejson
file = singlejson.load('auth.json', default_path='defaults/auth.json')
```
This way you can commit default files to your repository.
If the file doesn't exist or is corrupt,
the default file will be copied to the requested location.

For more detailed information,
visit the [documentation](https://singlejson.readthedocs.io/)


### Contributing:
This is just a fun project of mine mainly to try out python packaging. 
If you would like to contribute or have a feature-request,
please [open an issue or pull request](https://github.com/Qrashi/singlejson/issues/new).
