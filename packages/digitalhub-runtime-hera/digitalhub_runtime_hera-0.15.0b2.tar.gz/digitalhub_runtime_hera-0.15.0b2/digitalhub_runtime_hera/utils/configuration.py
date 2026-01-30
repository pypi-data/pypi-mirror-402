# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import Callable

from digitalhub.entities.workflow.crud import get_workflow
from digitalhub.stores.data.api import get_store
from digitalhub.utils.generic_utils import (
    decode_base64_string,
    extract_archive,
    import_function,
    requests_chunk_download,
)
from digitalhub.utils.git_utils import clone_repository
from digitalhub.utils.logger import LOGGER
from digitalhub.utils.uri_utils import (
    get_filename_from_uri,
    has_git_scheme,
    has_remote_scheme,
    has_s3_scheme,
    has_zip_scheme,
)

if typing.TYPE_CHECKING:
    from digitalhub.entities.workflow._base.entity import Workflow

DEFAULT_PY_FILE = "main.py"


def _parse_workflow_string(workflow_string: str) -> tuple[str, str, str]:
    """
    Parse workflow string into project, name, and UUID.

    Parameters
    ----------
    workflow_string : str
        Workflow string in format 'workflow://project/name:uuid'.

    Returns
    -------
    tuple[str, str, str]
        Project, name, and UUID.
    """
    splitted = workflow_string.split("://")[1].split("/")
    name, uuid = splitted[1].split(":")
    return splitted[0], name, uuid


def _get_workflow_file_path(path: Path, handler: str) -> Path:
    """
    Get workflow file path from handler.

    Parameters
    ----------
    path : Path
        Root path where the workflow source is located.
    handler : str
        Workflow handler.

    Returns
    -------
    Path
        Path to the workflow Python file.
    """
    if ":" in handler:
        handler_parts = handler.split(":")[0].split(".")
        return Path(path, *handler_parts).with_suffix(".py")
    return path.with_suffix(".py")


def _extract_handler_function_name(handler: str) -> str:
    """
    Extract function name from handler string.

    Parameters
    ----------
    handler : str
        Handler string.

    Returns
    -------
    str
        Function name.
    """
    if ":" in handler:
        return handler.split(":")[-1]
    return handler


def _download_and_extract_archive(source: str, path: Path) -> None:
    """
    Download and extract an archive from a URL or S3.

    Parameters
    ----------
    source : str
        Source URL (with zip+ scheme).
    path : Path
        Destination path.
    """
    clean_source = source.removeprefix("zip+")
    filename = path / get_filename_from_uri(source)

    if has_s3_scheme(clean_source):
        store = get_store(clean_source)
        store.get_s3_source(source, filename)
    else:
        requests_chunk_download(clean_source, filename)

    extract_archive(path, filename)
    filename.unlink()


def _save_base64_source(path: Path, base64_content: str) -> Path:
    """
    Save base64-encoded source to file.

    Parameters
    ----------
    path : Path
        Destination directory.
    base64_content : str
        Base64-encoded source code.

    Returns
    -------
    Path
        Path to the saved file (directory/main.py).
    """
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / DEFAULT_PY_FILE
    file_path.write_text(decode_base64_string(base64_content))
    return file_path


def _download_remote_source(path: Path, source: str) -> None:
    """
    Download source from remote URL (http/https).

    Parameters
    ----------
    path : Path
        Destination directory.
    source : str
        Remote source URL.
    """
    path.mkdir(parents=True, exist_ok=True)

    if has_zip_scheme(source):
        _download_and_extract_archive(source, path)
    else:
        filename = path / get_filename_from_uri(source)
        requests_chunk_download(source, filename)


def _download_s3_source(path: Path, source: str) -> None:
    """
    Download source from S3.

    Parameters
    ----------
    path : Path
        Destination directory.
    source : str
        S3 source URL (must be zip+s3:// scheme).
    """
    if not has_zip_scheme(source):
        raise RuntimeError("S3 source must be a zip file with scheme zip+s3://.")

    path.mkdir(parents=True, exist_ok=True)
    _download_and_extract_archive(source, path)


def _clone_git_source(path: Path, source: str) -> None:
    """
    Clone git repository.

    Parameters
    ----------
    path : Path
        Destination directory.
    source : str
        Git repository URL.
    """
    path.mkdir(parents=True, exist_ok=True)
    clone_repository(path, source)


def get_dhcore_workflow(workflow_string: str) -> Workflow:
    """
    Get DHCore workflow.

    Parameters
    ----------
    workflow_string : str
        Workflow string in format 'workflow://project/name:uuid'.

    Returns
    -------
    Workflow
        DHCore workflow.
    """
    project, name, uuid = _parse_workflow_string(workflow_string)
    LOGGER.info(f"Getting workflow {name}:{uuid}.")
    try:
        return get_workflow(name, project=project, entity_id=uuid)
    except Exception as e:
        msg = f"Error getting workflow {name}:{uuid}. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg) from e


def save_workflow_source(path: Path, source_spec: dict) -> Path:
    """
    Save workflow source from various sources.

    Parameters
    ----------
    path : Path
        Path where to save the workflow source.
    source_spec : dict
        Workflow source spec.

    Returns
    -------
    Path
        Path to the workflow Python file.
    """
    base64 = source_spec.get("base64")
    source = source_spec.get("source")
    handler: str = source_spec["handler"]

    # Base64-encoded source
    if base64 is not None:
        return _save_base64_source(path, base64)

    if source is None:
        raise RuntimeError("Workflow source not found in spec.")

    # Download source based on scheme
    if has_git_scheme(source):
        _clone_git_source(path, source)
    elif has_remote_scheme(source):
        _download_remote_source(path, source)
    elif has_s3_scheme(source):
        _download_s3_source(path, source)
    else:
        raise RuntimeError(f"Unable to collect source from: {source}")

    # Return path to the workflow file
    return _get_workflow_file_path(path, handler)


def get_hera_pipeline(name: str, source: Path, handler: str) -> Callable:
    """
    Get Hera pipeline by importing it from source.

    Parameters
    ----------
    name : str
        Name of the workflow.
    source : Path
        Path to the workflow source file.
    handler : str
        Handler of the workflow.

    Returns
    -------
    Callable
        Hera pipeline function.
    """
    try:
        function_name = _extract_handler_function_name(handler)
        return import_function(source, function_name)
    except Exception as e:
        msg = f"Error getting '{name}' Hera pipeline. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg) from e
