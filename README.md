# IdleUserExtend
Extension that fixes loading extensions from the user config file.

<!-- BADGIE TIME -->

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/CoolCat467/idleuserextend/main.svg)](https://results.pre-commit.ci/latest/github/CoolCat467/idleuserextend/main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![code style: black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<!-- END BADGIE TIME -->

## What does this extension do?
This IDLE extension patches IDLE to be able to properly load extensions
from the user configuration directory (`~/.idlerc/config-extensions.cfg`)
instead of forcing you to modify the root extension file.

## Installation
1) Go to terminal and install with `pip install idleuserextend`.
2) Run command `idleuserextend`. You should see the
following output: `Config should be good!`.
4) Open IDLE, go to `Options` -> `Configure IDLE` -> `Extensions`.
If everything went well, alongside `ZzDummy` there should be and
option called `idleuserextend`. All extensions are now able to load
from the user extension configuration file alone, no need to modify
`config-extensions.def` in `/usr/lib/python3.XX/idlelib` anymore!


## Information on options
`enable` toggles whether the extension is active or not.
