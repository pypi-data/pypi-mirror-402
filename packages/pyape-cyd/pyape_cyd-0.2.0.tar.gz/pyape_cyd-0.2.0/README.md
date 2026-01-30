# PyApe

**PyApe** is a Python client library and command-line interface (CLI) for interacting with [APE](https://gitlab-cyd.lhs.loria.fr/gorille/ape) server — the Gorille Server REST API.

- 🧰 The `ape` CLI tool for quick APE queries directly from your shell
- 📦 The `pyape` Python library to easily interact with APE directly from your other Python projects

---


## 🚀 Quick Start

### The `ape` CLI tool

```bash
ape --help
ape static myfile.bin
```

### The `pyape` Python library

```python
from pyape import Ape

ape = Ape(url="http://localhost", username="user", password="password")
response = ape.post_file_by_upload("myfile.bin")
print(response)
```


## 🧰 The `ape` command line tool

To install the `ape` command line tool you have two options:

### 1. Install from PyPi

If you don't have the source code, you can install the latest published version from PyPi:

```bash
# Install with pipx directly from PyPi
pipx install pyape-cyd

# Now you can use the CLI command from anywhere
ape --help
```

### 2. Install from source code

If you have the source code, you can install directly from the Git repository.
It's also usefull if you need to modify the package, this way you can directly see your local modifications.


```bash
# Clone the repo
git clone https://gitlab-cyd.lhs.loria.fr/gorille/pyape
cd pyape

# Install PyApe in editable mode from this local directory.
# This lets you make changes and test them immediately without reinstalling.
pipx install -e .

# Now you can use the CLI command from anywhere
ape --help
```

## 📦 The `pyape` Python library

### Why using this Python library

PyApe allows you to easily interact with APE from your other Python projects.

Library key features:

* Data validation thanks to Pydantic module:
    * Each returned JSON of APE is automatically parsed by Pydantic to "match" a specific Pydantic model. It means that if the format of a APE response change, you need to adjust the model to match with the response structure. It's a data validation feature, it's like a blueprint.
* APE responses as Python objects, Python dictionaries or JSON strings:
    * Thanks to Pydantic, you can use APE responses in the format that fit your needs: a real Python object, a dict or a JSON (see example bellow).
* APE error handling with Python exception:
    * The correct way to trigger, detect and handle errors in Python is to use Python Exceptions. With this library, if something goes wrong an `ApeException` Python exception will be raised. Thanks to this behaviour, you can call APE methods inside a classic try/catch to detect an error (see example bellow).

### How to import the library in your project

If you want to use PyApe in your Python project the recommended approach is to add it as a Git submodule. This keeps your codebase clean and allows you to edit PyApe independently.

#### 1. Add PyApe as a Git submodule

```bash
git submodule add https://gitlab-cyd.lhs.loria.fr/gorille/pyape external/pyape
```

This clones PyApe inside your project under `external/pyape`.

#### 2. Add the submodule as an editable dependency in your requirements.txt

In your main project’s requirements.txt, add the line:

```txt
-e external/pyape
```

#### 3. Initialize submodules and install dependencies

After cloning your main project repository, run:

```bash
# cd to the root of your Python project
git submodule update --init --recursive
pip install -r requirements.txt
```

This installs PyApe in editable mode from the local submodule directory.

### 4. Import and use PyApe in your code

You can now import Ape:

```python
from pyape import Ape
ape = Ape(url="http://localhost", username="user", password="password")
```

### How to use the library inside your project

#### Simple usage

```python
# Import Ape main class from ape lib
from pyape import Ape

# Create your ape object one time with the URL and the credentials of your instance server
ape = Ape("http://localhost/api", apikey="YOUR_API_KEY")

# Perform a request (e.g. static file analysis)
r = ape.post_file_by_upload("foo.exe")

# The returned variable result is not a dict, it's a Pydantic model (an ApeResponse).
# Because it's a Python object, you can access any attribute of this object (e.g. data attribute).

# Export the response as a dict:
print(magic_result.model_dump())

# Export the response as a valid JSON string:
print(magic_result.model_dump_json())

# For more information about Pydantic models see here:
# https://docs.pydantic.dev/latest/concepts/models/
```

#### Using an Ape instance from different locations

In a big project you may need to interact with Ape from multiple locations but you don't want to create a new `Ape` instance each time you want to request APE.
For this kind of usage you can use a Ape shared session like in the example above.

```python
# File: main.py

from pyape import init_ape_session

# Let's say you project entry point is in the main.py file.
# You can create your Ape instance from here
def main():
    init_ape_session("http://localhost/api", apikey="YOUR_API_KEY")
```


```python
# File: module1.py

from pyape import get_ape_session

# Then, in any other module, you can access your Ape instance created previously.
# Because the instance already exists, you don't need to provide the URL and your credentials.
def my_fun():
    ape = get_ape_session()
    r = ape.post_file_by_upload("foo.exe")

```


#### Handling Ape errors

If something is wrong during the HTTP request the Ape will raise an `ApeException` exception.
See the example below in order to detect and handle Ape library errors:

```python
from pyape import Ape

ape = Ape("http://localhost/api", apikey="YOUR_API_KEY")

try:
    r = ape.post_file_by_upload("foo.exe")
except ApeException as e:
    print(e)
```



## 🧱 Project Structure

```graphql
pyape/
├── pyape/
│   ├── __init__.py
│   ├── client.py         # Python API wrapper
│   └── cli.py            # CLI tool using Typer
├── pyproject.toml        # Packaging config
├── README.md
└── ...
```
