# IdleUserExtend
Extension that fixes loading extensions from the user config file.

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
