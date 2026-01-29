# f3ts-hardware-utils

FixturFab Functional Test System Hardware Utilities Library

## Connect and Control Test Hardware for your FixturFab Functional Test System

`f3ts-hardware-utils` is a Python module that contains the basic utilities for creating a
PCBA functional test system. This module contains classes for controlling all common test
hardware, including:

- Acroname Manufacturing Test Modules
- Feasa LED Analyzers
- FixturFab Test Instruments
- Segger J-Link Programmers
- Rigol Power Supplies and Programmable Loads
- Various USB Relay Hardware

## Installation into a Project using `poetry`

Install the package into your project using `poetry`:

```bash
poetry add f3ts-hardware-utils
```

## Documentation

The documentation for the package can be found [here](https://docs.fixturfab.com/f3ts-hardware-utils/).

## Development

### Environment Setup

[`poetry`](https://python-poetry.org/) is used for dependency management and
[`pre-commit`](https://pre-commit.com/) is used to identify simple issues
before submission for code review. Once installed, run the following commands
to setup your development environment:

```bash
poetry install
pre-commit install
```


### Making changes

Use the following process when making changes to the module:

1. Create new test cases
2. Write new feature code and/or bugfixes
3. Write documentation for new features
4. Run pre-commit checks and tests prior to committing

To run the pre-commit checks, simply run the following:

```bash
poetry run pre-commit run --all-files
```


### Code Quality Tools

#### `black`

[`black`]() is used for code formatting, this is configured within `pyproject.toml`

To run `black` manually, run:

```bash
poetry run black .
```

#### `flake8`

[`flake8`](https://flake8.pycqa.org/en/latest/) is used to enforce additional
style guidelines.

To run `flake8` manually, run:

```bash
poetry run flake8 ./pytest_f3ts
```

#### `isort`

[`isort`](https://pycqa.github.io/isort/) is used to automatically reformat
python module import statements.

To run `isort` manually, run:

```bash
poetry run isort .
```


#### `pre-commit`

To automatically check if code is ready to be committed and pushed to Gitlab
[`pre-commit`](https://pre-commit.com/) is used. This is configured via the
`.pre-commit-config.yml` file.

To run `pre-commit` manually, run:

```bash
poetry run pre-commit run --all-files
```


### Documentation Generation

[`mkdocs`](https://www.mkdocs.org/) is utilized along with [`mkdocs-material`](https://github.com/squidfunk/mkdocs-material) to generate documentation for
this project.

The `docs` directory contains the general structure for the documentation in
the form of markdown files. To autogenerate additional documentation from
docstrings, the [`mkdocstrings`](https://mkdocstrings.github.io/) module is
used.

#### Developing documentation with the live server

When creating additional documentation it's useful to run the `mkdocs` server
which will live-reload the webpages as you make changes. To start this server,
run the following in a terminal: ### `pre-commit`


```bash
poetry run mkdocs serve
```

#### Adding a new file for autodocumentation

To add a new python file to the autodocumentation, open the `docs/reference.md`
file. Add a new header to the file, and then add the line
`::: f3ts_hardware_utils.{new_file_name}`, this will signal to `mkdocstrings` to
process the new file when building the documentation

### Manually building and uploading a wheel

```bash
poetry config repositories.f3ts-hardware-utils https://us-west1-python.pkg.dev/test-runner-404519/pytest-f3ts/

# On windows you will need to run the following command as two separate commands
# and paste the token into the password prompt for the second command.
gcloud auth print-access-token | poetry config http-basic.f3ts-hardware-utils oauth2accesstoken

poetry publish --repository pytest-f3ts --build
```


## Pipeline Setup

The pipeline is configured via the `.gitlab-ci.yml` file. The pipeline is
configured to run the following stages:

- `linting`: Runs the `black`, `flake8`, and `isort` checks
    - Occurs on all merge requests and is required to pass before a merge
      request can be merged
- `version`: Runs the `gen-semver.py` command to update the version number
    - Occurs after a merge request is accepted.
    - `[skip ci]` is added to a new Git Commit to prevent the pipeline from
      running again
- `build`: Builds the package and uploads it to the Gitlab package registry
    - Triggered by new tags, which are created by the `version` stage
