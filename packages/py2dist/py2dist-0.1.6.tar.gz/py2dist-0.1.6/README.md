# py2dist

[中文文档](README_zh.md)

py2dist is a tool that uses Cython to compile Python source code into binary extension modules (`.so`/`.pyd`). It is designed to simply protect source code from modification and is suitable for scenarios such as releasing Python projects or building Docker service images.

## Features

- Support Linux, Mac, Windows platforms.
- Support compiling single `.py` files or entire directories into binary files.
- Preserve directory structure, automatically copy other files to the output directory.
- Support excluding specific files or directories.
- Automatically detect and use `ccache` to accelerate compilation.
- Get a small performance boost from Cython compilation.
- Provide both CLI and Python API two usage methods.

## Installation

```bash
pip3 install py2dist
```

It is recommended to use [`uv`](https://docs.astral.sh/uv/) to install and manage virtual environments, and pin the Python version to avoid inconsistencies between the compilation result and the actual runtime environment. Taking Python 3.12 as an example:

```bash
uv python pin 3.12
uv venv
uv add --dev py2dist
```

> It is not recommended to use `uv tool install py2dist` for installation, as this will invoke the system Python version for compilation, leading to inconsistency between the compilation result and the actual runtime virtual environment.

## Important Note: Python Version Consistency

The compiled binary extension modules (`.so`/`.pyd`) are bound to a specific Python version. **You must ensure that the Python version used for compilation is exactly the same as the Python version used at runtime** (including minor version numbers; for example, 3.10 and 3.11 are incompatible).

If the versions do not match, you may encounter errors like the following when importing the module:
`ImportError: ... undefined symbol: _PyThreadState_UncheckedGet`
or
`ModuleNotFoundError: No module named ...`

## Usage

### Command Line Interface (CLI)

The default output directory is `dist` / `{directory name specified by -d}`, but you can also specify the output directory using the `-o` parameter.

Compile a single file:
```bash
python3 -m py2dist -f myscript.py
```

Or use the `uv` command:
```bash
uv run py2dist -f myscript.py
```

The output file location will be `dist/myscript.so`.

Compile an entire directory:
```bash
python3 -m py2dist -d myproject
```

Or use the `uv` command:
```bash
uv run py2dist -d myproject
```

The output location will be `dist/myproject`, and non-`.py` files will be automatically copied to the output directory.

## Example Usage

For example, if I have a Python FastAPI project and I want to package it as a Docker image while protecting the source code from modification, I can use py2dist to compile the core code directory of the project into binary extension modules, and then copy them into the Docker image. Direct release is also possible, the principle is similar.

> In actual projects, I am more accustomed to using files like `uv`, `pyproject.toml`, `.python-version` to control project dependencies and Python versions. Docker image builds can also install tools like `ccache`, `uv` to optimize the workflow. This demonstration simplifies the process and will not expand on this; you can research improvements on your own.

### Example Project Environment

- `ccache`: Recommended installation to accelerate compilation speed for subsequent project changes. `py2dist` will automatically identify and use it.
- `python3.12`: The Python version used during project compilation. Therefore, the Docker image must also use this Python version, otherwise an error will occur.

### Project Example Structure:

```
myproject/
├── Makefile (Project build file)
├── run.py (Server startup file, cannot be compiled)
├── requirements.txt
├── Dockerfile
├── server/ (Project code directory, the compilation target)
│   ├── __init__.py (Must exist for every module, content can be empty)
│   ├── main.py (FastAPI main entry file)
│   ├── utils.py
│   ├── router/ (Module router directory)
│   │   ├── __init__.py (Must exist for every module, content can be empty)
│   │   └── user.py
│   ├── static/ (Other files, will be copied as is)
│   │   └── image.png
│   └── templates/ (Other files, will be copied as is)
│       ├── index.html
│       └── about.html
├── tests/
│   └── test_main.py
├── models/
└   └── ...
```

Sample `run.py`:
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=3000)
```

> 1. The `__init__.py` file must exist and its content can be empty. This allows it to be recognized as a module after compilation.
>
> 2. An uncompiled `run.py` file is needed to start the server.
>
> 3. According to general standards, it is not recommended to place resource files in the source code directory; they are usually placed in a separate directory for reference. However, for demonstration purposes, some resource files are placed here to demonstrate the automatic copy function.
>

So you can write the `Makefile` like this:

```makefile
.PHONY: install compile build

install:
    pip3 install py2dist

compile:
    python3 -m py2dist -d server

build: compile
    docker build -t myproject .
```

Write the `Dockerfile` like this:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY models /app/models

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip3 install -r requirements.txt

COPY dist/server /app/server
COPY run.py /app/run.py

EXPOSE 3000
CMD ["python3", "/app/run.py"]
```

Then run the command:
```bash
cd myproject
make build
```

This will build the release version of the image.
At this point, if we check the file structure inside the image, it looks like this:

```
/app/
├── run.py
├── server/
│   ├── __init__.py
│   ├── main.so
│   ├── utils.so
│   ├── router/
│   │   ├── __init__.py
│   │   └── user.so
│   ├── static/
│   │   └── image.png
│   └── templates/
│       ├── index.html
│       └── about.html
├── models/
└   └── ...
```

This achieves the goal of simply protecting source code from modification.

If you don't want to use a Docker image, you can directly package and release the project, or use a similar process; the principle is the same.

First modify the `run.py` file and add the following code at the beginning of the file:
```python
import sys
import os

# ================= Import lib =================

current_dir = os.path.dirname(os.path.abspath(__file__))

lib_path = os.path.join(current_dir, "lib")

if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# ================= End of Import lib =================
```

And modify the `server/main.py` file, adding the following code at the beginning of the file:
```python
import sys
import os

# ================= Import lib =================

current_dir = os.path.dirname(os.path.abspath(__file__))

lib_path = os.path.join(current_dir, "../lib")

if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# ================= End of Import lib =================
```
The purpose is to allow the Python interpreter to recognize third-party library files. Next, package and release using a command similar to the following:

```bash
cd myproject
make compile
mkdir -p build/lib
cp -r dist/server build/server
cp run.py build/run.py
pip install -r requirements.txt --target "./build/lib" --python-version "3.12" --only-binary=":all:"
tar -czvf myproject.tar.gz build
```

You can release the project to any server. Of course, this method also requires a Python 3.12 environment with the same version number in the runtime environment. You can also place a portable Python 3.12 environment yourself, or use tools like `uv` to control project dependencies and Python versions, which will not be expanded here.

### Advanced

Arguments:
- `-f, --file`: Specify a single `.py` file to compile.
- `-d, --directory`: Specify the directory to compile.
- `-o, --output`: Output directory (default is `dist`).
- `-m, --maintain`: Files or directories to exclude (comma-separated).
- `-x, --nthread`: Number of compilation threads (default is 1).
- `-q, --quiet`: Quiet mode.
- `-r, --release`: Release mode (cleans up temporary build files).
- `-c, --ccache`: Use ccache (auto-detect by default, or specify path).

### Python API

```python
from py2dist import compile_file, compile_dir

# Compile a single file
compile_file("myscript.py", output_dir="dist")

# Compile a directory
compile_dir(
    "myproject",
    output_dir="dist",
    exclude=["tests", "setup.py"],
    nthread=4
)
```

## Others

### Project Origin

Sometimes, you need to release a Python project, but you don't want customers to modify the source code themselves and cause issues. Therefore, you need a simple way to protect the source code files.

Because the philosophy of Python is to distribute source code, CPython does not provide real compilation functionality. However, many people have worked in this area.

I've compared several popular projects:
- [`Nuitka`](https://nuitka.net/) performs real compilation by translating Python to C through special optimizations. However, it often requires extra adaptation for certain third-party packages, and when there are many packages, compilation can be very time-consuming. I used it for a while but eventually gave up.
- [`Pyarmor`](https://github.com/dashingsoft/pyarmor) specializes in obfuscation and encryption. It works as expected, but I didn't choose it because I don't need many of its obfuscation and encryption features, and it's commercial software that requires purchasing a machine license.
- [`Cython`](https://cython.org/) is fully compatible with modern Python versions and ecosystems. Although compiling pure `.py` code does not truly translate it into C, it is sufficient for the general purpose of protecting source code from being modified.

I've used this workflow for a while without any issues, so I developed this project as a package for easier installation and release. 😊

This project does not involve encryption or obfuscation; you can optimize it yourself if you need such features.

### Thanks

- [Cython](https://cython.org/) for empowering the combination of Python and C.
- This project is based on [`py2sec`](https://github.com/cckuailong/py2sec) scripts, and has been optimized and improved on top of it. Thanks to the author of this excellent project.
