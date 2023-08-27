"""Idle User Extend.

Extension that fixes loading extensions from the user config file.
"""

# Programmed by CoolCat467

from __future__ import annotations

__title__ = "idleuserextend"
__author__ = "CoolCat467"
__license__ = "GPLv3"
__version__ = "0.0.0"


import contextlib
import os
import sys
from collections import ChainMap
from collections.abc import Callable
from functools import wraps
from tkinter import StringVar
from typing import ClassVar

import idlelib.configdialog
from idlelib.config import IdleConf, idleConf
from idlelib.pyshell import PyShellEditorWindow


def get_required_config(
    values: dict[str, str],
    bind_defaults: dict[str, str],
) -> str:
    """Get required configuration file data."""
    config = ""
    # Get configuration defaults
    settings = "\n".join(
        f"{key} = {default}" for key, default in values.items()
    )
    if settings:
        config += f"\n[{__title__}]\n{settings}"
        if bind_defaults:
            config += "\n"
    # Get key bindings data
    settings = "\n".join(
        f"{event} = {key}" for event, key in bind_defaults.items()
    )
    if settings:
        config += f"\n[{__title__}_cfgBindings]\n{settings}"
    return config


def check_installed() -> bool:
    """Make sure extension installed."""
    # Get list of system extensions
    extensions = set(idleConf.defaultCfg["extensions"]) | set(
        idleConf.userCfg["extensions"],
    )
    ex_defaults = idleConf.userCfg["extensions"].file

    # Import this extension (this file),
    module = __import__(__title__)

    # Get extension class
    if not hasattr(module, __title__):
        print(
            f"ERROR: Somehow, {__title__} was installed improperly, "
            f"no {__title__} class found in module. Please report "
            "this on github.",
            file=sys.stderr,
        )
        sys.exit(1)

    cls = getattr(module, __title__)

    # Get extension class keybinding defaults
    required_config = get_required_config(
        getattr(cls, "values", {}),
        getattr(cls, "bind_defaults", {}),
    )

    # If this extension not in there,
    if __title__ not in extensions:
        # Tell user how to add it to system list.
        print(f"{__title__} not in system registered extensions!")
        print(
            f"Please run the following command to add {__title__} "
            + "to system extensions list.\n",
        )
        # Make sure line-breaks will go properly in terminal
        add_data = required_config.replace("\n", "\\n")
        # Tell them the command
        print(f"echo -e '{add_data}' >> {ex_defaults}")
        print()
    else:
        print(f"Configuration should be good! (v{__version__})")
        return True
    return False


def ensure_section_exists(section: str) -> bool:
    """Ensure section exists in user extensions configuration.

    Returns True if edited.
    """
    if section not in idleConf.GetSectionList("user", "extensions"):
        idleConf.userCfg["extensions"].AddSection(section)
        return True
    return False


def ensure_values_exist_in_section(
    section: str,
    values: dict[str, str],
) -> bool:
    """For each key in values, make sure key exists. Return if edited.

    If not, create and set to value.
    """
    need_save = False
    for key, default in values.items():
        value = idleConf.GetOption(
            "extensions",
            section,
            key,
            warn_on_default=False,
        )
        if value is None:
            idleConf.SetOption("extensions", section, key, default)
            need_save = True
    return need_save


def get_mangled(obj: object, attribute: str) -> str:
    """Get mangled attribute name for object."""
    if attribute.endswith("__"):
        return attribute
    if not attribute.startswith("__"):
        return attribute
    return f"_{obj.__class__.__name__}{attribute}"


@wraps(getattr(idleConf, get_mangled(idleConf, "__GetRawExtensionKeys")))
def get_raw_extension_keys(extension: str) -> dict[str, list[str]]:
    """Return dict {configurable extension event : keybinding list}.

    Events come from default config extension_cfgBindings section.
    Keybindings list come from the splitting of GetOption, which
    tries user config before default config.
    """
    ext_bindings_section = f"{extension}_cfgBindings"
    extension_keys: dict[str, list[str]] = {}
    if idleConf.defaultCfg["extensions"].has_section(ext_bindings_section):
        raw_event_names = idleConf.defaultCfg["extensions"].GetOptionList(
            ext_bindings_section,
        )
        event_names = [
            name for name in raw_event_names if isinstance(name, str)
        ]
        for event_name in event_names:
            binding = str(
                idleConf.GetOption(
                    "extensions",
                    ext_bindings_section,
                    event_name,
                    default="",
                ),
            ).split()
            event = f"<<{event_name}>>"
            extension_keys[event] = binding
    if idleConf.userCfg["extensions"].has_section(ext_bindings_section):
        event_names = idleConf.userCfg["extensions"].GetOptionList(
            ext_bindings_section,
        )
        for event_name in event_names:
            binding = str(
                idleConf.GetOption(
                    "extensions",
                    ext_bindings_section,
                    event_name,
                    default="",
                ),
            ).split()
            event = f"<<{event_name}>>"
            extension_keys[event] = binding
    return extension_keys


setattr(
    idleConf,
    get_mangled(idleConf, "__GetRawExtensionKeys"),
    get_raw_extension_keys,
)


@wraps(idleConf.GetExtensionKeys)
def get_extension_keys(extension: str) -> dict[str, list[str] | str]:
    """Return dict: {configurable extension event : active keybinding}.

    Events come from default config extension_cfgBindings section.
    Keybindings come from GetCurrentKeySet() active key dict,
    where previously used bindings are disabled.
    """
    ext_bindings_section = f"{extension}_cfgBindings"
    current_keyset = idleConf.GetCurrentKeySet()
    extension_keys = {}

    event_names = set()
    if idleConf.userCfg["extensions"].has_section(ext_bindings_section):
        event_names |= set(
            idleConf.userCfg["extensions"].GetOptionList(
                ext_bindings_section,
            ),
        )
    if idleConf.defaultCfg["extensions"].has_section(ext_bindings_section):
        event_names |= set(
            idleConf.defaultCfg["extensions"].GetOptionList(
                ext_bindings_section,
            ),
        )

    for event_name in event_names:
        event = f"<<{event_name}>>"
        binding = current_keyset.get(event, None)
        if binding is None:
            continue
        extension_keys[event] = binding
    return extension_keys


idleConf.GetExtensionKeys = get_extension_keys


@wraps(idleConf.GetExtensionBindings)
def get_ext_bindings(extension: str) -> dict[str, list[str]]:
    """Return dict {extension event : active or defined keybinding}."""
    bindings_section = f"{extension}_bindings"
    extension_keys: dict[str, list[str]] = idleConf.GetExtensionKeys(extension)
    # add the non-configurable bindings

    values = []
    if idleConf.userCfg["extensions"].has_section(bindings_section):
        values.append(
            idleConf.userCfg["extensions"].GetOptionList(bindings_section),
        )
    if idleConf.defaultCfg["extensions"].has_section(bindings_section):
        values.append(
            idleConf.defaultCfg["extensions"].GetOptionList(bindings_section),
        )

    event_names = ChainMap(*values)

    if event_names:
        for event_name in event_names:
            binding = idleConf.GetOption(
                "extensions",
                bindings_section,
                event_name,
                default="",
            ).split()
            event = f"<<{event_name}>>"
            extension_keys[event] = binding
    return extension_keys


idleConf.GetExtensionBindings = get_ext_bindings


@wraps(idleConf.LoadCfgFiles)
def load_cfg_files() -> None:
    """Load all configuration files."""
    for key in idleConf.defaultCfg:
        idleConf.defaultCfg[key].Load()
    for key in idleConf.userCfg:
        idleConf.userCfg[key].Load()


idleConf.LoadCfgFiles = load_cfg_files


class ExtPage(idlelib.configdialog.ExtPage):  # type: ignore  # Cannot subclass "ExtPage", is "Any"
    """Modified copy of ExtPage with patched load_extensions."""

    def load_extensions(self) -> None:
        """Fill self.extensions with data from the default and user configs."""
        self.extensions: dict[str, list[dict[str, object]]] = {}

        for ext_name in idleConf.GetExtensions(active_only=False):
            # Former built-in extensions are already filtered out.
            self.extensions[ext_name] = []

        for ext_name in self.extensions:
            default = set(self.ext_defaultCfg.GetOptionList(ext_name))
            user = set(self.ext_userCfg.GetOptionList(ext_name))
            opt_list = sorted(default | user)

            # Bring 'enable' options to the beginning of the list.
            enables = [
                opt_name
                for opt_name in opt_list
                if str(opt_name).startswith("enable")
            ]
            for opt_name in enables:
                opt_list.remove(opt_name)
            opt_list = enables + opt_list

            for opt_name in opt_list:
                def_str = self.ext_defaultCfg.Get(ext_name, opt_name, raw=True)
                if opt_name in user:
                    def_str = self.ext_userCfg.Get(
                        ext_name,
                        opt_name,
                        raw=True,
                    )
                else:
                    def_str = self.ext_defaultCfg.Get(
                        ext_name,
                        opt_name,
                        raw=True,
                    )
                def_obj: bool | int | str
                try:
                    def_obj = {"True": True, "False": False}[def_str]
                    opt_type = "bool"
                except KeyError:
                    try:
                        def_obj = int(def_str)
                        opt_type = "int"
                    except ValueError:
                        def_obj = def_str
                        opt_type = None
                try:
                    value = self.ext_userCfg.Get(
                        ext_name,
                        opt_name,
                        type=opt_type,
                        raw=True,
                        default=def_obj,
                    )
                    if opt_name in user:
                        value = self.ext_userCfg.Get(
                            ext_name,
                            opt_name,
                            type=opt_type,
                            raw=True,
                            default=def_obj,
                        )
                    else:
                        value = self.ext_defaultCfg.Get(
                            ext_name,
                            opt_name,
                            type=opt_type,
                            raw=True,
                            default=def_obj,
                        )
                except ValueError:  # Need this until .Get fixed.
                    value = def_obj  # Bad values overwritten by entry.
                var = StringVar(self)
                var.set(str(value))
                self.extensions[ext_name].append(
                    {
                        "name": opt_name,
                        "type": opt_type,
                        "default": def_str,
                        "value": value,
                        "var": var,
                    },
                )

    def set_extension_value(self, section: str, opt: IdleConf) -> bool:
        """Return True if the configuration was added or changed.

        If the value is the same as the default, then remove it
        from user config file.
        """
        name = opt["name"]
        default = opt["default"]
        value = opt["var"].get().strip() or default
        opt["var"].set(value)

        # Set the option.
        return bool(self.ext_userCfg.SetOption(section, name, value))

    def save_all_changed_extensions(self) -> None:
        """Save configuration changes to the user config file.

        Attributes accessed:
            extensions

        Methods
        -------
            set_extension_value
        """
        for ext_name in self.extensions:
            self.extensions[ext_name]
            for opt in self.extensions[ext_name]:
                self.set_extension_value(ext_name, opt)
        self.ext_userCfg.Save()


idlelib.configdialog.ExtPage = ExtPage


def remove_keybindings(editwin: PyShellEditorWindow) -> Callable[[], None]:
    """Remove the keybindings before they are changed."""

    @wraps(editwin.RemoveKeybindings)
    def inner() -> None:
        """Remove keybinds before changed."""
        # Called from configdialog.py
        editwin.mainmenu.default_keydefs = (
            keydefs
        ) = idleConf.GetCurrentKeySet()
        for event, keylist in keydefs.items():
            with contextlib.suppress(ValueError):
                editwin.text.event_delete(event, *keylist)

        for extension_name in editwin.get_standard_extension_names():
            xkeydefs = idleConf.GetExtensionBindings(extension_name)
            if xkeydefs:
                for event, keylist in xkeydefs.items():
                    with contextlib.suppress(ValueError):
                        editwin.text.event_delete(event, *keylist)

    return inner


# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.


class idleuserextend:  # noqa: N801
    """Extension that fixes loading extensions from the user config file."""

    __slots__ = ("editwin",)

    # Extend the file and format menus.
    menudefs: ClassVar = []

    # Default values for configuration file
    values: ClassVar = {
        "enable": "True",
        "enable_editor": "True",
        "enable_shell": "False",
    }
    # Default key binds for configuration file
    bind_defaults: ClassVar = {}

    # Class attributes
    idlerc_folder = os.path.expanduser(idleConf.userdir)

    def __init__(self, editwin: PyShellEditorWindow) -> None:
        """Initialize the settings for this extension."""
        self.editwin: PyShellEditorWindow = editwin
        # print(f"{__title__} Initialize")

        # for name, instance in editwin.extensions.items():
        #     keydefs = idleConf.GetExtensionBindings(name)
        #     for keydef in keydefs:
        #         editwin.text.unbind(keydef)
        #     if keydefs:
        #         for event, keylist in keydefs.items():
        #             if keylist:
        #                 editwin.text.event_add(event, *keylist)
        #         for vevent in keydefs:
        #             methodname = vevent.replace("-", "_")
        #             while methodname[:1] == '<':
        #                 methodname = methodname[1:]
        #             while methodname[-1:] == '>':
        #                 methodname = methodname[:-1]
        #             methodname = f'{methodname}_event'
        #             if hasattr(instance, methodname):
        #                 editwin.text.bind(vevent, getattr(instance, methodname))
        editwin.RemoveKeybindings = remove_keybindings(editwin)

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"{self.__class__.__name__}({self.editwin!r})"

    @classmethod
    def ensure_bindings_exist(cls) -> bool:
        """Ensure key bindings exist in user extensions configuration.

        Return True if need to save.
        """
        if not cls.bind_defaults:
            return False

        need_save = False
        section = f"{cls.__name__}_cfgBindings"
        if ensure_section_exists(section):
            need_save = True
        if ensure_values_exist_in_section(section, cls.bind_defaults):
            need_save = True
        return need_save

    @classmethod
    def ensure_config_exists(cls) -> bool:
        """Ensure required configuration exists for this extension.

        Return True if need to save.
        """
        need_save = False
        if ensure_section_exists(cls.__name__):
            need_save = True
        if ensure_values_exist_in_section(cls.__name__, cls.values):
            need_save = True
        return need_save

    @classmethod
    def reload(cls) -> None:
        """Load class variables from configuration."""
        # Ensure file default values exist so they appear in settings menu
        save = cls.ensure_config_exists()
        if cls.ensure_bindings_exist() or save:
            idleConf.SaveUserCfgFiles()

        # Reload configuration file
        idleConf.LoadCfgFiles()

        # For all possible configuration values
        for key, default in cls.values.items():
            # Set attribute of key name to key value from configuration file
            if key not in {"enable", "enable_editor", "enable_shell"}:
                value = idleConf.GetOption(
                    "extensions",
                    cls.__name__,
                    key,
                    default=default,
                )
                setattr(cls, key, value)


idleuserextend.reload()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    check_installed()
