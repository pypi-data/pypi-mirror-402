#__init__.py    30Oct2025  crs
# Command line scripts for graphics_braille
import os
import shutil
import pathlib
import importlib.resources

import graphics_braille
from graphics_braille.onedrive_ck import is_desktop_on_onedrive

def main_function():
    print("Installation Run")

def gbhelp():
    print("""
          gb, gbhelp - List graphics-braille commands
          gbreadme - Display README.md
          gbfiles - add user test files to user desktop
          gbtest - Do simple program test
          gbtest2 - Do simple program test - spokes
          """)

def gbreadme():
    import os
    os.system("distinfo_readme graphics_braille")

def gbfiles():
    """ Place/Update user files on Desktop
    """
    package_name = "graphics_braille"
    package_traversable = importlib.resources.files(package_name)
    print(f"{package_traversable = }")
    data_dir_base = "gb_exercises"
    data_path = package_traversable.parent / data_dir_base
    print(f"Path to data directory: {data_path}")    
    source_dir = str(data_path)
    print(f"{source_dir =}")                                    
    desktop = pathlib.Path.home() / 'Desktop'
    on_onedrive, desktop_location = is_desktop_on_onedrive()
    if on_onedrive:
        print(f"OneDrive {desktop_location = }")
        desktop = desktop_location
    try:
        # Copy the directory tree, allowing existing directories
        src = source_dir
        dst = os.path.join(desktop, os.path.basename(src))
        os.makedirs(dst, exist_ok=True) # Ensure the parent exists if needed
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"Successfully copied '{src}' to '{dst}'.")
    except Exception as e:
        print(f"An error occurred: {e}"
              f" in copy '{src}' to '{dst}'.")
    
    
    
def gbtest():
    import graphics_braille.z_show_square_loop_colors_braille
    
def gbtest2():
    import graphics_braille.show_spokes_braille
