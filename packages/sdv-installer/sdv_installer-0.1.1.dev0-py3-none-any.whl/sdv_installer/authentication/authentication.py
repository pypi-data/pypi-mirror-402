"""Licensing authentication module."""

import json
from functools import wraps

import requests
from requests.exceptions import RequestException

from sdv_installer import config
from sdv_installer.utils import (
    get_password_input,
    print_empty_username_or_license_key,
    print_failed_to_connect,
    print_invalid_credentials,
)


def authenticate_user_and_license_key(username, license_key):
    """Authenticate the user and license key by sending a request to the authentication API.

    Constructs an authentication request using the provided username and license key,
    sends it to the appropriate API endpoint, and returns a boolean indicating whether
    the authentication was successful.

    Args:
        username (str):
            The username to authenticate.
        license_key (str):
            The license key to authenticate.

    Raises:
        InvalidLoginCredentials:
            If the user has provided invalid login credentials.

    Returns:
        bool:
            True if authentication is successful, False otherwise.
    """
    post_data = {'username': username, 'license_key': license_key}
    try:
        response = requests.post(
            config.API_VALIDATE, json=post_data, headers=config.HEADERS, timeout=config.TIMEOUT
        )
    except RequestException:
        print_failed_to_connect()
        return False

    response_dict = response.json()
    valid = response_dict.get('valid', False)
    authenticated = bool(response.status_code == requests.codes.ok and valid)
    if not authenticated:
        print_invalid_credentials()

    return authenticated


def _load_credentials_from_file(filepath):
    try:
        with open(filepath, 'r') as file:
            credentials = json.load(file)
            return credentials

    except FileNotFoundError as e:
        raise ValueError(f'The credentials file {filepath} was not found.') from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f'Failed to decode the json file {filepath}') from e


def authenticate(function):
    """Authenticate wrapper to be used by other functions."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        username = kwargs.get('username')
        license_key = kwargs.get('license_key')
        credentials = kwargs.get('credentials')
        if (username or license_key) and credentials:
            raise ValueError(
                'You have provided both --credentials and --username/--license-key flags. '
                'Please choose only one of these methods for authentication.'
            )

        elif username or license_key:
            username_no_lk = username is not None and license_key is None
            lk_no_username = license_key is not None and username is None
            if username_no_lk or lk_no_username:
                raise ValueError(
                    'You must provide both the --username and --license-key flags for '
                    'authentication.'
                )

        elif credentials:
            credentials_json = _load_credentials_from_file(credentials)
            username = credentials_json['username']
            license_key = credentials_json['license_key']
            kwargs['username'] = username
            kwargs['license_key'] = license_key

        else:
            username = input('Username: ') or ''
            username = username.strip()

            license_key = get_password_input('License Key: ') or ''
            license_key = license_key.strip()

            if not username or not license_key:
                print_empty_username_or_license_key()
                return

            kwargs['username'] = username
            kwargs['license_key'] = license_key

        authenticated = authenticate_user_and_license_key(username, license_key)
        if authenticated:
            return function(*args, **kwargs)

    return wrapper
