#add_src_dir.py
""" Add this file's source directory
to sys.path, if not already in sys.path
This module was created as a workaround to the
lack of our pypi installation site directory path
enabling visibility to our packages modules
This module expects to reside in our package's
site directory.  If that directory is not
found in sys.path the directory is added to sys.path
"""
import sys
import os
print(f"Initial sys.path:\n    {"\n    ".join(sys.path)}")

src_file = os.path.abspath(__file__)
print(f"add_src_dir file: {src_file}")
src_path = os.path.dirname(src_file)
if src_path not in sys.path:
    print(f"Inserting source directory {src_path}")
    sys.path.insert(0, src_path)
    print(f"sys.path:\n    {"\n    ".join(sys.path)}")

if __name__ == '__main__':

    import add_src_dir
    print(f"Selftest for {__file__}") 