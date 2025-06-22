"""Idle User Extend.

Extension that fixes loading extensions from the user config file.
"""

# Programmed by CoolCat467

from __future__ import annotations

# Idle User Extend
# Copyright (C) 2023-2025  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "idleuserextend"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.3"


import idlelib.configdialog
import sys
from functools import wraps
from idlelib.config import idleConf
from idlelib.editor import get_accelerator, prepstr
from tkinter import StringVar
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from idlelib.pyshell import PyShellEditorWindow


def check_installed() -> bool:
    """Make sure extension installed."""
    # Get list of system extensions
    extensions = set(idleConf.defaultCfg["extensions"]) | set(
        idleConf.userCfg["extensions"],
    )

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

    # If this extension not in there,
    if __title__ not in extensions:
        # Tell user how to add it to system list.
        print(f"{__title__} not in system registered extensions!")
        print("This should not be possible! If you see this message,")
        print("please report this issue on Github!")
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


def yield_string_entries(
    iterable: Iterable[object],
) -> Generator[str, None, None]:
    """Yield string entries from an iterable."""
    for entry in iterable:
        if isinstance(entry, str):
            yield entry


# [misc] Type of decorated function contains type "Any"
@wraps(getattr(idleConf, get_mangled(idleConf, "__GetRawExtensionKeys")))
def get_raw_extension_keys(extension: str) -> dict[str, list[str]]:  # type: ignore[misc]
    """Return dict {configurable extension event : keybinding list}.

    Events come from default config extension_cfgBindings section.
    Keybindings list come from the splitting of GetOption, which
    tries user config before default config.
    """
    ext_bindings_section = f"{extension}_cfgBindings"
    extension_keys: dict[str, list[str]] = {}
    if idleConf.defaultCfg["extensions"].has_section(ext_bindings_section):
        event_names = yield_string_entries(
            idleConf.defaultCfg["extensions"].GetOptionList(
                ext_bindings_section,
            ),
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
    if idleConf.userCfg["extensions"].has_section(ext_bindings_section):
        event_names = yield_string_entries(
            idleConf.userCfg["extensions"].GetOptionList(
                ext_bindings_section,
            ),
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


def get_user_extension_event_names(section: str) -> set[str]:
    """Return user extension event names."""
    event_names: set[str] = set()
    if idleConf.userCfg["extensions"].has_section(section):
        event_names.update(
            yield_string_entries(
                idleConf.userCfg["extensions"].GetOptionList(section),
            ),
        )
    return event_names


def get_default_extension_event_names(section: str) -> set[str]:
    """Return default extension event names."""
    event_names: set[str] = set()
    if idleConf.defaultCfg["extensions"].has_section(section):
        event_names.update(
            yield_string_entries(
                idleConf.defaultCfg["extensions"].GetOptionList(
                    section,
                ),
            ),
        )
    return event_names


@wraps(idleConf.GetExtensionKeys)
def get_extension_keys(extension: str) -> dict[str, list[str]]:
    """Return dict: {configurable extension event : active keybinding}.

    Events come from default config extension_cfgBindings section.
    Keybindings come from GetCurrentKeySet() active key dict,
    where previously used bindings are disabled.
    """
    ext_bindings_section = f"{extension}_cfgBindings"
    current_keyset = idleConf.GetCurrentKeySet()
    extension_keys: dict[str, list[str]] = {}

    event_names = get_user_extension_event_names(ext_bindings_section)
    event_names |= get_default_extension_event_names(ext_bindings_section)

    for event_name in event_names:
        event = f"<<{event_name}>>"
        binding = current_keyset.get(event, None)
        if binding is None:
            continue
        extension_keys[event] = binding
    return extension_keys


idleConf.GetExtensionKeys = get_extension_keys  # type: ignore[method-assign,assignment]


def get_extension_event_key_bindings(
    extension: str,
    event_names: Iterable[str],
) -> dict[str, list[str]]:
    """Return dict {extension event : active or defined keybinding}."""
    extension_keys: dict[str, list[str]] = idleConf.GetExtensionKeys(extension)
    bindings_section = f"{extension}_bindings"

    for event_name in event_names:
        binding = idleConf.GetOption(
            "extensions",
            bindings_section,
            event_name,
            default="",
        )
        if not isinstance(binding, str):
            print(
                f"[{__title__}] Non-string binding in idle extensions config: {bindings_section}.{event_name}",
            )
            continue
        event = f"<<{event_name}>>"
        extension_keys[event] = binding.split()
    return extension_keys


@wraps(idleConf.GetExtensionBindings)
def get_extension_bindings(extension: str) -> dict[str, list[str]]:
    """Return dict {extension event : active or defined keybinding}."""
    bindings_section = f"{extension}_bindings"
    # add the non-configurable bindings

    event_names = get_user_extension_event_names(bindings_section)
    event_names |= get_default_extension_event_names(bindings_section)

    return get_extension_event_key_bindings(extension, event_names)


idleConf.GetExtensionBindings = get_extension_bindings  # type: ignore[method-assign,assignment]


def get_user_added_extension_bindings(extension: str) -> dict[str, list[str]]:
    """Return dict {extension event : active or defined keybinding}."""
    bindings_section = f"{extension}_bindings"
    # add the non-configurable bindings

    event_names = get_user_extension_event_names(bindings_section)
    event_names -= get_default_extension_event_names(bindings_section)

    return get_extension_event_key_bindings(extension, event_names)


@wraps(idleConf.LoadCfgFiles)
def load_cfg_files() -> None:
    """Load all configuration files."""
    for key in idleConf.defaultCfg:
        idleConf.defaultCfg[key].Load()
    # might have different keys hence patching
    for key in idleConf.userCfg:
        idleConf.userCfg[key].Load()


idleConf.LoadCfgFiles = load_cfg_files  # type: ignore[method-assign]

original_ext_page = idlelib.configdialog.ExtPage


class ExtPage(idlelib.configdialog.ExtPage):
    """Modified copy of ExtPage with patched load_extensions."""

    def load_extensions(self) -> None:
        """Fill self.extensions with data from the default and user configs."""
        self.extensions: dict[
            str,
            list[dict[str, str | int | StringVar | None]],
        ] = {}

        for ext_name in idleConf.GetExtensions(active_only=False):
            # Former built-in extensions are already filtered out.
            self.extensions[ext_name] = []

            default = set(self.ext_defaultCfg.GetOptionList(ext_name))
            user = set(self.ext_userCfg.GetOptionList(ext_name))
            opt_list = sorted(yield_string_entries(default | user))

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
                    def_obj = {"True": True, "False": False}[str(def_str)]
                    opt_type = "bool"
                except KeyError:
                    try:
                        def_obj = int(def_str)
                        opt_type = "int"
                    except ValueError:
                        def_obj = def_str
                        opt_type = None
                try:
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

    def set_extension_value(
        self,
        section: str,
        opt: dict[str, str | int | StringVar | None],
    ) -> bool:
        """Return True if the configuration was added or changed.

        If the value is the same as the default, then remove it
        from user config file.
        """
        name = opt["name"]
        assert isinstance(name, str)
        default = opt["default"]
        assert isinstance(default, (str, int)) or default is None
        var = opt["var"]
        assert isinstance(var, StringVar)
        value = var.get().strip() or str(default)
        var.set(value)

        # Only save option in user config if it differs from the default
        if self.ext_defaultCfg.has_section(section) and value == default:
            return bool(self.ext_userCfg.RemoveOption(section, name))

        # Set the option.
        return bool(self.ext_userCfg.SetOption(section, name, value))


#     def save_all_changed_extensions(self) -> None:
#         """Save configuration changes to the user config file.
#
#         Attributes accessed:
#             extensions
#
#         Methods
#         -------
#             set_extension_value
#
#         """
#         for ext_name in self.extensions:
#             for opt in self.extensions[ext_name]:
#                 self.set_extension_value(ext_name, opt)
#         self.ext_userCfg.Save()


# Cannot assign to a type
idlelib.configdialog.ExtPage = ExtPage  # type: ignore[misc]


def find_added_bindings(
    new: dict[str, list[str]],
    old: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Return the bindings that were added compared to old."""
    sections_new = set(new)
    sections_old = set(old)
    new_sections = sections_new - sections_old
    existing_sections = sections_new & sections_old

    added_bindings: dict[str, list[str]] = {
        section: new[section] for section in new_sections
    }
    for section in existing_sections:
        bindings_new = set(new[section])
        bindings_old = set(old[section])
        added = bindings_new - bindings_old
        if added:
            added_bindings[section] = list(added)

    return added_bindings


def apply_keybindings_for_previous(editwin: PyShellEditorWindow) -> None:
    """Apply the virtual keybindings for extensions that didn't load properly.

    Also update hotkeys to current keyset.

    Modified version of idlelib.editor.ApplyKeybindings.
    """
    new_default_keydefs = idleConf.GetCurrentKeySet()
    added_bindings = find_added_bindings(
        new_default_keydefs,
        editwin.mainmenu.default_keydefs,
    )
    # print(f'[{__title__}] {added_bindings = }')
    editwin.apply_bindings(added_bindings)
    editwin.mainmenu.default_keydefs = new_default_keydefs  # type: ignore[attr-defined]
    # Already handled adding extension keybindings as a part of prior
    # for extension_name in editwin.get_standard_extension_names():
    #     extension_keydefs = get_user_added_extension_bindings(extension_name)
    #     print(f'[{__title__}] {extension_name = } {extension_keydefs = }')
    #     if extension_keydefs:
    #         editwin.apply_bindings(extension_keydefs)

    # Update menu accelerators.
    menu_event_dict: dict[str, dict[str, str]] = {}
    for group_title, bindings in editwin.mainmenu.menudefs:
        menu_event_dict[group_title] = {}
        for item in bindings:
            if not item:
                continue
            label, virt_event = item
            menu_event_dict[group_title][prepstr(label)[1]] = virt_event
    for menubar_item, menu in editwin.menudict.items():
        end = menu.index("end")
        if end is None:
            # Skip empty menus
            continue
        end += 1
        for index in range(end):
            if menu.type(index) != "command":
                continue
            accel = menu.entrycget(index, "accelerator")
            if not accel:
                continue
            item_name = menu.entrycget(index, "label")
            items = menu_event_dict.get(menubar_item)
            if not items:
                continue
            event = items.get(item_name, None)
            if not event:
                continue
            accel = get_accelerator(editwin.mainmenu.default_keydefs, event)
            menu.entryconfig(index, accelerator=accel)


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

    def __init__(self, editwin: PyShellEditorWindow) -> None:
        """Initialize the settings for this extension."""
        self.editwin: PyShellEditorWindow = editwin
        # print(f"[{__title__}] Initialize")

        # Properly bind extensions that didn't load completely before
        apply_keybindings_for_previous(editwin)

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
        # print(f"[{__title__}] reload fires")
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

    # def close(self) -> None:
    #     """Called when and IDLE window is closing."""
    #     print("[idleuserextend] close fires")

    def on_reloading(self) -> None:
        """Idlereload integration, fired when about to reload."""
        setattr(
            idleConf,
            get_mangled(idleConf, "__GetRawExtensionKeys"),
            get_raw_extension_keys.__wrapped__,
        )
        idleConf.GetExtensionKeys = get_extension_keys.__wrapped__  # type: ignore[method-assign]
        idleConf.GetExtensionBindings = get_extension_bindings.__wrapped__  # type: ignore[method-assign]
        idleConf.LoadCfgFiles = load_cfg_files.__wrapped__  # type: ignore[method-assign]
        idlelib.configdialog.ExtPage = original_ext_page  # type: ignore[misc]


idleuserextend.reload()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    check_installed()
