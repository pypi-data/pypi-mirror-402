"""Resource utilities for ligo-scald.
"""

import sys

if sys.version_info >= (3, 9):
    # use importlib.resources for Python >= 3.9
    from importlib import resources

    def get_resource_path(resource_name):
        """Get the path to a resource within this package."""
        # Use the package name string directly
        package_files = resources.files('ligo.scald')
        resource_path = package_files / resource_name

        # Use context manager for proper resource handling
        with resources.as_file(resource_path) as path:
            return str(path)

else:
    # fallback to pkg_resources for Python < 3.9
    import pkg_resources

    def get_resource_path(resource_name):
        """Get the path to a resource within this package."""
        return pkg_resources.resource_filename('ligo.scald', resource_name)
