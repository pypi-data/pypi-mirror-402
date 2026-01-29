from django.apps import apps
from django.conf import settings


def get_apps(metadata, key="apps", exclude_site_packages=False):
    """
    Generate a list of the apps for the site, and add it to the metadata.

    With exclude_site_packages set to True only apps for the site will be
    listed. All dependencies, Django, etc. will be excluded.

    Args:
        metadata: the dictionary to add the list of apps to
        key: The key to use for the apps list (default: 'apps')
        exclude_site_packages: Include only apps for the site (default: False)

    Returns:
        The modified metadata dict
    """
    results = []

    for app in apps.get_app_configs():
        if exclude_site_packages and 'site-packages' in app.path:
            continue
        results.append(app.name)

    metadata[key] = results
    return metadata


def get_models(metadata, key="models", exclude_site_packages=False):
    """
    Generate a list of the models for the site, and add it to the metadata.

    With exclude_site_packages set to True only models for the site will be
    listed. All models from dependencies, Django, etc. will be excluded.

    Args:
        metadata: the dictionary to add the list of models to
        key: The key to use for the models list (default: 'models')
        exclude_site_packages: Include only models for the site (default: False)

    Returns:
        The modified metadata dict
    """
    results = []

    for app in apps.get_app_configs():
        if exclude_site_packages and 'site-packages' in app.path:
            continue
        for model in app.get_models():
            results.append(str(model._meta))

    metadata[key] = results
    return metadata


def get_settings(metadata, key='settings'):
    """
    Generate a dict containing all Django settings and add it to the target dict.

    Args:
        metadata: The dictionary to add settings to
        key: The key to use for the settings dict (default: 'settings')

    Returns:
        The modified metadata dict
    """
    settings_dict = {}

    for setting in dir(settings):
        if setting.isupper():
            settings_dict[setting] = getattr(settings, setting)

    metadata[key] = settings_dict
    return metadata
