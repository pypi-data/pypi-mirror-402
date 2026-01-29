"""Tests for ligo.scald.resources module."""

import os

from ligo.scald import resources


def test_get_template_file_path():
    """Test accessing a template file via get_resource_path."""
    # Test accessing a known template file
    template_path = resources.get_resource_path('templates/dashboard.html')

    # Verify the path is returned as a string
    assert isinstance(template_path, str)

    # Verify the path points to an existing file
    assert os.path.exists(template_path)

    # Verify it's the correct file
    assert template_path.endswith('dashboard.html')

    # Verify the file contains expected content
    with open(template_path, 'r') as f:
        content = f.read()
        # Check for some expected content in the dashboard template
        assert 'dashboard' in content.lower() or 'html' in content.lower()


def test_get_template_directory_path():
    """Test accessing the templates directory via get_resource_path."""
    templates_dir = resources.get_resource_path('templates')

    # Verify the path is returned as a string
    assert isinstance(templates_dir, str)

    # Verify the path points to an existing directory
    assert os.path.exists(templates_dir)
    assert os.path.isdir(templates_dir)

    # Verify it contains expected template files
    dashboard_file = os.path.join(templates_dir, 'dashboard.html')
    assert os.path.exists(dashboard_file)
