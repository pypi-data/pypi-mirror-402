"""System requirements utility functions."""

import platform
import re
import subprocess
import sys
import sysconfig

import pip
from packaging.tags import sys_tags
from packaging.version import Version

from sdv_installer.constants import (
    MAX_PYTHON_VERSION,
    MIN_OS_VERSIONS,
    MIN_PIP_VERSION,
    MIN_PYTHON_VERSION,
    REQUIRED_BITNESS,
    SUPPORTED_ARCHITECTURES,
    SUPPORTED_LINUX_DISTROS,
    SUPPORTED_OSES,
)
from sdv_installer.utils.console_utils import print_message

LINUX_OS_RELEASE_FILE = '/etc/os-release'


def _normalize_kernel_version(kernel_version):
    parts = kernel_version.split('.')
    normalized_version = []
    for part in parts:
        num = ''
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break

        if not num:
            break

        normalized_version.append(num)

    return '.'.join(normalized_version)


def _get_linux_distro_version():
    with open(LINUX_OS_RELEASE_FILE) as f:
        data = dict(line.strip().split('=', 1) for line in f if '=' in line)

    linux_distro_version = data.get('VERSION_ID', '').strip('"')
    return Version(linux_distro_version)


def get_os_info():
    """Detects the operating system type and version.

    Returns:
        Tuple[str, str, Optional[str], bool]: A tuple containing:
            - os_system (str):
                'macOS', 'Linux', or other OS name.
            - os_version (str):
                The complete OS version (e.g., '15.6.1').
            - linux_distro (Optional[str]):
                Pretty name of the Linux distribution, if applicable.
            - is_linux (bool):
                Whether the OS is Linux.
    """
    system = platform.system()
    version = platform.version()
    is_linux = sys.platform == 'linux'
    linux_distro = None

    if sys.platform == 'darwin':
        version = subprocess.check_output(['sw_vers', '-productVersion'], text=True).strip()
        system = 'macOS'

    elif is_linux:
        version = _normalize_kernel_version(platform.release())
        output = subprocess.run(
            f'cat {LINUX_OS_RELEASE_FILE}', shell=True, capture_output=True, text=True
        )
        match = re.search(r'PRETTY_NAME="(.*)"', output.stdout.strip())
        linux_distro = match.group(1) if match else None

    return system, version, linux_distro, is_linux


def get_architecture():
    """Determines the system architecture (e.g., arm64, x86_64).

    Returns:
        str: The system's architecture identifier.
    """
    if platform.system().lower() == 'windows':
        return sysconfig.get_platform()

    return subprocess.check_output(['uname', '-m'], text=True).strip().lower()


def get_current_platform_tag():
    """Returns the normalized platform tag for the current system."""
    return sysconfig.get_platform().replace('-', '_').replace('.', '_')


def get_python_version_code():
    """Returns the current Python major and minor version as a tuple."""
    major = sys.version_info.major
    minor = sys.version_info.minor
    return Version(f'{major}.{minor}')


def get_system_info():
    """Collects all relevant system information for SDV Installer validation.

    Returns:
        dict: A dictionary with system attributes including:
            - os_system (str)
            - os_version (str)
            - linux_distro (Optional[str])
            - architecture (str)
            - python_version (str)
            - system_bit (str)
            - pip_version (str)
            - platform_tag (str)
            - processor (str)
            - is_linux (bool)
    """
    os_system, os_version, linux_distro, is_linux = get_os_info()
    arch = get_architecture()
    python_version = platform.python_version()
    bitness = '64-bit' if sys.maxsize > 2**32 else '32-bit'
    pip_version = pip.__version__
    processor = platform.processor()
    platform_tag = get_current_platform_tag()

    return {
        'os_system': os_system,
        'os_version': os_version,
        'linux_distro': linux_distro,
        'architecture': arch,
        'python_version': python_version,
        'system_bit': bitness,
        'pip_version': pip_version,
        'platform_tag': platform_tag,
        'processor': processor,
        'is_linux': is_linux,
    }


def get_user_supported_tags():
    """Retrieves the set of platform tags supported by the current Python environment.

    These tags are used to determine compatibility with precompiled wheels.

    Returns:
        Set[str]:
            A set of supported platform tag strings.
    """
    return {tag.platform for tag in sys_tags()}


def get_pip_version_code():
    """Retrive the `pip` version of the current environment."""
    return Version(pip.__version__)


def validate_system_requirements(info):
    """Validates the current system against the minimum technical requirements.

    Args:
        info (dict): A dictionary containing system info (as from `get_system_info`).

    Returns:
        List[str]: A list of keys that failed validation (e.g., ['python_version']).
    """
    errors = []

    # Validate Python version
    python_version = get_python_version_code()
    if python_version < MIN_PYTHON_VERSION or python_version > MAX_PYTHON_VERSION:
        errors.append('python_version')

    # Validate system bitness
    if info['system_bit'] != REQUIRED_BITNESS:
        errors.append('system_bit')

    # Validate OS
    if info['os_system'] not in SUPPORTED_OSES:
        errors.append('os_system')

    # Validate os minimal version
    if Version(info['os_version']) < MIN_OS_VERSIONS.get(info['os_system'], Version('0')):
        errors.append('os_version')

    # Validate architecture
    if info['architecture'] not in SUPPORTED_ARCHITECTURES:
        errors.append('architecture')

    # Validate pip minimal version
    if Version(info['pip_version']) < MIN_PIP_VERSION:
        errors.append('pip_version')

    if info.get('linux_distro'):
        linux_distro = info.get('linux_distro', '').lower()
        min_version = None
        linux_version = _get_linux_distro_version()
        if 'ubuntu' in linux_distro:
            min_version = SUPPORTED_LINUX_DISTROS.get('ubuntu')
        elif 'debian' in linux_distro:
            min_version = SUPPORTED_LINUX_DISTROS.get('debian')

        if min_version and linux_version < min_version:
            errors.append('linux_distro')

    return errors


def print_check_results():
    """Runs the system checks and prints the result in a user-friendly format."""
    print_message('Verifying system requirements for SDV Enterprise: \n')
    info = get_system_info()
    errors = validate_system_requirements(info)

    def mark(key):
        return ' (!)' if key in errors else ''

    print_message(f'Operating system: {info["os_system"]}{mark("os_system")}')
    print_message(f'OS Version: {info["os_version"]}{mark("os_version")}')
    if info['is_linux'] and info['linux_distro']:
        print_message(f'Linux Distribution: {info["linux_distro"]}{mark("linux_distro")}')

    print_message(f'Architecture: {info["architecture"]}{mark("architecture")}')
    print_message(f'Python Version: {info["python_version"]}{mark("python_version")}')
    print_message(f'System bit: {info["system_bit"]}{mark("system_bit")}')
    print_message(f'Pip version: {info["pip_version"]}{mark("pip_version")}')

    print_message(f'\nResult: {"Passed" if not errors else "Failed"}')
    if not errors:
        print_message('Your system meets the technical requirements for SDV Enterprise.')
        sys.exit(0)
    else:
        print_message(
            'Your system may not meet the technical requirements for SDV Enterprise. '
            'Please check the items marked by (!) and try updating the SDV '
            "Installer if something doesn't seem right."
        )
        print_message('The most up-to-date requirements are on the SDV Enterprise docs site.')
        sys.exit(1)
