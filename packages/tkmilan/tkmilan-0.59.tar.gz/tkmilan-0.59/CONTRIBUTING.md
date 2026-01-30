## Development

The Python version selection if done on `Makefile`, `PYTHON_VERSION`. This is
used on all supported systems. The virtual environment setup is fully
automated.

### Linux

To start developing on Linux, make sure you have all the necessary programs installed:

#### Python

The required Python version must be available as `python$PYTHON_VERSION`.

#### First Time Setup

After cloning the project, open a terminal there and run:

```sh
make
```

This might take a while, but it will setup every dependency, including the
LaTeX environment to create PDF files.

If you have any issue with dependencies, you can delete everything using:

```sh
make clean-all
```

Once this is done, you can setup everything again.

#### Workflow

To run the main Python entrypoint, use:

```sh
./run
```

To run it on a loop, and wait when there's an error return value, use:

```sh
./run forever
```

Both these accept more arguments, passed to the entrypoint.

To run the project inside an IDE, choose one of the IDE scripts:

```sh
./run-ide-spyder
./run-ide-vscode
```

This will automatically setup and install the IDE if possible and needed.
Extra arguments are passed to the IDE.

If you need to activate the virtual environment only, use:

```sh
make bash
```

To load the bash completion files, use `source release/completions.bash`.

Run `exit` to return to the original shell.

To create all important documentation, use:

```sh
make docs
```

This generates HTML documentation in `dist/docs/html`, open the `index.html` file to check it.
Other documents are generated in `dist/docs`:
- `dist/docs/latex` has the PDF version of the documentation.
  Not supported on Windows for now.
  See the "Disable automatic PDF generation" section below for instructions on
  how to disable this, if needed.

Optionally, define `BASEURL` environment variable if you know what the base URL
should be when serving the generated HTML.

Run all the configured tests, using:

```sh
make -j test
```

The `-j` option runs all tests in parallel. The output might be a bit jumbled
up...

### Windows

To start developing on Windows, make sure you have all the necessary programs installed:

#### Visual C++ Redistributable

Install the latest Visual C++ Redistributable package, available
[here](https://aka.ms/vs/16/release/vc_redist.x64.exe).

#### Python

Check the required Python version above. The 64 bits version is preferred, but both should work.

The required Python version must be installed using the [Python Windows
Download](https://www.python.org/downloads/windows/) binaries. 
If in doubt, select the "Windows x86-64 executable installer" link.

Make sure the `py` helper is available. This can be tested by running on a new
command line:

    py -$PYTHON_VERSION --version

#### First Time Setup

After cloning the project, open a terminal there and run:

```
setup-dev
```

This might take a while, but it will setup every dependency.

This only needs to be done **ONCE**. It should only be re-run if the
dependencies change.

If you have any issue with dependencies, you can delete everything using:

```
clean-dev
```

Once this is done, you can setup everything again.

#### First Time IDE Setup

Follow the "First Time Setup" above, but running the IDE script variants.

You can also just double-click them on Explorer.

To setup every dependency for all supported IDE, use:

```
setup-ide
```

Or alternatively, for a specific IDE only:

```
setup-ide-spyder
setup-ide-vscode
```

#### Workflow

To run the main Python entrypoint, use:

```
run-dev
```

If you need to activate the virtual environment only, use:

```
run-cli
```

After that, all entrypoints should be available for testing.
When the entrypoint list changes, you need to do the First Time Setup again.

If the IDE is already configured correctly, choose the IDE to open:

```
run-ide-spyder
run-ide-vscode
```

Run all the configured tests, using:

```
test.cmd
```

## Release

The release process supports generating Debug and Release binaries.

In terms of Python code, we leverage the `__debug__` Python feature. Release
binaries are optimised, debug binaries are not.
See the Python documentation for
[`__debug__`](https://docs.python.org/3/library/constants.html#__debug__),
[`-O`](https://docs.python.org/3/using/cmdline.html#cmdoption-O), and
[`PYTHONOPTIMIZE`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONOPTIMIZE).

### Linux

The release process is divided into three steps.

Note the OS-specific Release Files can be generated for many OS, depending on
the support requirements.

#### OS-specific Release Files

For OS-specific files (usually binaries), this process must run on an instance of that specific OS.

Currently, this means generating the Python binaries. Run:

```sh
make release-python-release
```

This generates a tarball with the current host name on the `dist` folder.

#### Common Files

The common files are the same everywhere, so they can be generated only once.
Usually, this can be done on the development machine.

Run:

```sh
make release-common
```

This generates a tarball with a `_` suffix on the `dist` folder. This is to
mark them as incomplete release tarball, not to be confused with the final
release.

#### Putting it all together

Move all OS-specific and common release tarballs to the same machine. Usually,
this is the development machine.

Once all release tarballs are in place on the `dist` folder, run:

```sh
make release
```

This merges all tarballs into a single release tarball, supporting all OS
corresponding to the release files.

The files created in `dist` can be now be published.

#### Debug Release

For debug binaries (just for the Python code, in a single executable), run:

```sh
make release-python-release
```

The files created in `dist` can be now be published.

### Windows

The release process is fully automated.
You can either open a new `cmd` window and run the command, or just
double-click them on Explorer.

To create a full release, run:

```
build-release.cmd
```

To create debug binaries (just the Python code, in a single executable), run:

```
build-debug.cmd
```

All files are created on the `dist` folder.

## Extra Development Features

### Templates

There are templates to be copied around on the `release/templates` folder.

### Blocklist for Packages

- **File**: `release/unrequirements.txt`

List of packages to uninstall when setting up the virtual environment. Useful
mostly for long-lived projects, and when the venv is always reused.

Optional, create if needed.

Only supported on Windows.

### Virtual Environment Issues

If you have issues with the virtual environment, you can try to reload it. This
should reinstall the core packages that setup the virtual environment itself.
If all else fails, just delete everything and start over.

Reloading the virtual environment depends on the OS:

#### Linux

You can reload the virtual environment by running `make venv-update`. To
recreate the LaTeX environment, run `make vlatex-update`.

#### Windows

You can reload the virtual environment by running `setup-dev.cmd` again.

### Office Documents

- **Files**: Office Files in `docs` (no children directories)
  - Run `release/list-docs-office` to list all the known office files.

List of office files to distribute as PDF files on the documentation.
These are automatically converted using the headless version of LibreOffice. If
the files exist, LibreOffice must be installed to convert them during the
release.

Optional, create if needed.

To use this, create all important documentation as usual (`make docs`).
Requires LibreOffice to be installed (`soffice`).

Only supported on Linux, for now.
