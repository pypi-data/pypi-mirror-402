#onedrive_ck.py 19Nov2025  from google search

import os
from glob import glob

def is_desktop_on_onedrive():
    """
    Determines if the Desktop folder is located within the OneDrive directory.
    """
    try:
        # Attempt to find the Desktop path using glob, which can handle OneDrive's relocated Desktop
        # This looks for a "Desktop" folder within any subfolder of the user's home directory.
        desktop_path_glob_list = glob(os.path.expanduser("~\\*\\Desktop"))

        if desktop_path_glob_list:
            # If glob found a path, check if it contains "OneDrive"
            # This handles cases where Desktop is directly under a OneDrive folder
            for path in desktop_path_glob_list:
                if "OneDrive" in path:
                    return True, path
            
            # If glob found a path but it's not directly in "OneDrive",
            # it might be a standard Desktop path or a different redirection.
            # We can then compare it to the "default" Desktop location.
            default_desktop_path = os.path.expanduser("~\\Desktop")
            if default_desktop_path not in desktop_path_glob_list:
                # If the glob path is different from the default, and not directly OneDrive,
                # it's still possible it's a OneDrive-managed path, but we need more robust checks.
                # For simplicity here, we'll assume a direct "OneDrive" check is sufficient for this method.
                pass

        # If glob returns an empty list, it means the Desktop is likely in the default location
        # or a location not covered by the glob pattern.
        # In this case, we check the standard Desktop path for "OneDrive".
        standard_desktop_path = os.path.expanduser("~\\Desktop")
        if "OneDrive" in standard_desktop_path:
            return True, standard_desktop_path
            
        return False, standard_desktop_path # Return False and the standard path if not found in OneDrive

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, None

if __name__ == "__main__":
    on_onedrive, desktop_location = is_desktop_on_onedrive()
    if on_onedrive:
        print(f"The Desktop is managed by OneDrive. Location: {desktop_location}")
    else:
        print(f"The Desktop is not managed by OneDrive. Location: {desktop_location}")
