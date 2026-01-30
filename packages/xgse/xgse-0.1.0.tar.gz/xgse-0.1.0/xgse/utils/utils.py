import hashlib
import importlib
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Any, Dict, Tuple, Union
from typing import List, Optional


SUPPORTED_SCRIPT_EXT = ('.py', '.sh', '.js')
SUPPORTED_READ_EXT = ('.md', '.txt', '.py', '.json', '.yaml', '.yml', '.sh',
                      '.js', '.html', '.xml')


def find_skill_dir(root: Union[str, List[str]]) -> List[str]:
    """
    Find all skill directories containing SKILL.md

    Args:
        root: Root directory to search

    Returns:
        list: List of skill directory paths
    """
    if isinstance(root, str):
        root_paths = [Path(root).resolve()]
    else:
        root_paths = [Path(p).resolve() for p in root]

    folders = []

    for root_path in root_paths:
        if not root_path.exists():
            continue
        for item in root_path.rglob('SKILL.md'):
            if item.is_file():
                folders.append(str(item.parent))

    return list(dict.fromkeys(folders))


def extract_implementation(content: str) -> Tuple[str, List[Any]]:
    """
    Extract IMPLEMENTATION content and determine execution scenario.
        e.g. <IMPLEMENTATION> ... </IMPLEMENTATION>

    Args:
        content: Full text containing IMPLEMENTATION tag

    Returns:
        Tuple of (scenario_type, results)
            scenario_type: 'script_execution', 'code_generation', or 'unable_to_execute'
            results: List of parsed results based on scenario
    """
    impl_content: str = extract_by_tag(text=content, tag='IMPLEMENTATION')
    results: List[Any] = []
    # Scenario 1: Script Execution
    try:
        results: List[Dict[str, Any]] = json.loads(impl_content)
    except Exception as e:
        logging.debug(f'Failed to parse IMPLEMENTATION as JSON: {str(e)}')

    if len(results) > 0:
        return 'script_execution', results

    # Scenario 2: No Script Execution, output JavaScript or HTML code blocks
    results: List[str] = re.findall(r'```(html|javascript)\s*\n(.*?)\n```',
                                    impl_content, re.DOTALL)
    if len(results) > 0:
        return 'code_generation', results

    # Scenario 3: Unable to Execute Any Script, provide reason (string)
    return 'unable_to_execute', [impl_content]


def extract_packages_from_code_blocks(text) -> List[str]:
    """
    Extract ```packages ... ``` content from input text.

    Args:
        text (str): Text containing packages code blocks

    Returns:
        list: List of packages, e.g. ['numpy', 'torch', ...]
    """
    pattern = r'```packages\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)

    results = []
    for packages_str in matches:
        try:
            cleaned_packages_str = packages_str.strip()
            results.append(cleaned_packages_str)
        except Exception as e:
            raise RuntimeError(
                f'Failed to decode shell command: {e}\nProblematic shell string: {packages_str}'
            )

    results = '\n'.join(results).splitlines()
    return results


def extract_cmd_from_code_blocks(text) -> List[str]:
    """
    Extract ```shell ... ``` code block from text.

    Args:
        text (str): Text containing shell code blocks

    Returns:
        list: List of parsed str
    """
    pattern = r'```shell\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)

    results = []
    for shell_str in matches:
        try:
            cleaned_shell_str = shell_str.strip()
            results.append(cleaned_shell_str)
        except Exception as e:
            raise RuntimeError(
                f'Failed to decode shell command: {e}\nProblematic shell string: {shell_str}'
            )

    return results


def copy_with_exec_if_script(src: str, dst: str):
    """
    Copy file from src to dst. If it's a script file, add execute permission.

    Args:
        src (str): Source file path
        dst (str): Destination file path
    """
    shutil.copy2(src, dst)
    # Add execute permission if it's a script file
    if Path(src).suffix in SUPPORTED_SCRIPT_EXT:
        st = os.stat(src)
        os.chmod(dst, st.st_mode | 0o111)


def str_to_md5(text: str) -> str:
    """
    Converts a given string into its corresponding MD5 hash.

    This function encodes the input string using UTF-8 and computes the MD5 hash,
    returning the result as a 32-character hexadecimal string.

    Args:
        text (str): The input string to be hashed.

    Returns:
        str: The MD5 hash of the input string, represented as a hexadecimal string.

    Example:
        >>> str_to_md5("hello world")
        '5eb63bbbe01eeed093cb22bb8f5acdc3'
    """
    text_bytes = text.encode('utf-8')
    md5_hash = hashlib.md5(text_bytes)
    return md5_hash.hexdigest()


def is_package_installed(package_or_import_name: str) -> bool:
    """
    Checks if a package is installed by attempting to import it.

    Args:
    package_or_import_name: The name of the package or import as a string.

    Returns:
        True if the package is installed and can be imported, False otherwise.
    """
    return importlib.util.find_spec(package_or_import_name) is not None


def install_package(package_name: str,
                    import_name: Optional[str] = None,
                    extend_module: str = None):
    """
    Check and install a package using pip.

    Note: The `package_name` may not be the same as the `import_name`.

    Args:
        package_name (str): The name of the package to install (for pip install).
        import_name (str, optional): The name used to import the package.
                                    If None, uses package_name. Defaults to None.
        extend_module (str, optional): The module to extend, e.g. `pip install modelscope[nlp]` when set to 'nlp'.
    """
    # Use package_name as import_name if not provided
    if import_name is None:
        import_name = package_name

    if extend_module:
        package_name = f'{package_name}[{extend_module}]'

    if not is_package_installed(import_name):
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', package_name])
        logging.info(f'Package {package_name} installed successfully.')
    else:
        logging.info(f'Package {import_name} is already installed.')


def extract_by_tag(text: str, tag: str) -> str:
    """
    Extract content enclosed by specific XML-like tags from the given text. e.g. <TAG> ...content... </TAG>

    Args:
        text (str): The input text containing the tags.
        tag (str): The tag name to search for.

    Returns:
        str: The content found between the specified tags, or an empty string if not found.
    """
    pattern = fr'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return ''


def valid_repo_id(repo_id: str) -> bool:
    """
    Validate the format of a ModelScope repository ID.

    Args:
        repo_id (str): The repository ID to validate. e.g. owner/model_name, owner/model_name/subfolder

    Returns:
        bool: True if the repo_id is valid, False otherwise.
    """
    if not repo_id:
        return False

    repo_id_parts: List[str] = repo_id.split('/')
    if len(repo_id_parts) in (2, 3) and all(repo_id_parts):
        return True

    return False

