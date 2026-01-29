""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""

import avesterra.attributions as attributions
from avesterra.avial import *
from avesterra.predefined import file_outlet
import avesterra.aspects as aspects




AvFile = AvEntity


def create_file(
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    mode: AvMode = AvMode.NULL,
    outlet: AvEntity = NULL_ENTITY,
    server: AvEntity = NULL_ENTITY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvFile:
    """Create a new file entity in AvesTerra

    Creates a new file entity using the file adapter. The file entity
    can be used to store and manage file data within the AvesTerra system.
    File entities support attributions for metadata like mode, time, hash,
    and version.

    Parameters
    __________
    name : AvName
        Name of the file entity to create
    key : AvKey
        Key identifier for the file entity
    mode : AvMode
        File mode/permissions for the created file
    outlet : AvEntity
        file adapter to use; defaults to predefined file_outlet
    server : AvEntity
        Server entity to associate with the file
    authorization : AvAuthorization
        Authorization required to create the file entity; the authorization must be present on the file adapter

    Returns
    _______
    AvFile
        The created file entity

    Examples
    ________

    >>> 
    >>> authorization: AvAuthorization
    >>> # Create a simple file
    >>> file = files.create_file(name="example.txt", authorization=authorization)
    >>> print(f"Created file: {file}")
    """
    adapter = file_outlet if outlet == NULL_ENTITY else outlet
    value = invoke_entity(
        adapter,
        AvMethod.CREATE,
        name=name,
        key=key,
        context=AvContext.AVESTERRA,
        category=AvCategory.AVESTERRA,
        klass=AvClass.FILE,
        mode=mode,
        ancillary=server,
        authorization=authorization,
    )
    return value.decode_entity()


def delete_file(file: AvFile, authorization: AvAuthorization = NULL_AUTHORIZATION):
    """Delete a file entity from AvesTerra

    Permanently removes a file entity and its associated data from the
    AvesTerra system. This operation cannot be undone.

    Parameters
    __________
    file : AvFile
        File entity to delete
    authorization : AvAuthorization
        Authorization required to delete the file entity; the authorization must be present on the file adapter and the file itself

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> # Delete a file entity
    >>> files.delete_file(file=file, authorization=authorization)
    """
    invoke_entity(file, AvMethod.DELETE, authorization=authorization)


def download_file(
    file: AvFile,
    name: str,
    timeout: AvTimeout,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Download file data from AvesTerra entity to local filesystem

    Retrieves the data stored in a file entity and writes it to the local
    filesystem. The downloaded file will have the same permissions as stored
    in the file entity's MODE attribution, or default permissions if no
    mode is set.

    Parameters
    __________
    file : AvFile
        File entity to download data from
    name : str
        Local filename to save the downloaded data
    timeout : AvTimeout
        Maximum time to wait for the download operation
    authorization : AvAuthorization
        Authorization required to read from the file entity; the authorization must be present on the file adapter and the file itself

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> timeout: AvTimeout = 30.0
    >>> # Download file to local filesystem
    >>> files.download_file(
    ...     file=file,
    ...     name="downloaded_file.txt",
    ...     timeout=timeout,
    ...     authorization=authorization
    ... )


    IOError
        When the downloaded data cannot be written to local filesystem
    """
    try:
        data = read_data(entity=file, timeout=timeout, authorization=authorization)
    except Exception as e:
        raise AvialError(f"Failed to download file {file}({name}): {str(e)}") from e

    try:
        with open(f"{name}", "wb") as f:
            f.write(data)
    except Exception as e:
        raise IOError(
            f"Failed to write file {file}({name}) to directory {getcwd()}/{name}"
        )

    try:
        mode = attributions.get_attribution(
            entity=file, attribute=AvAttribute.MODE, authorization=authorization
        ).decode()
        mode = int(mode)
    except Exception as e:
        mode = 0o664
    os.chmod(f"{name}", mode)


def upload_file(
    file: AvFile,
    path: str,
    version: str,
    timeout: AvTimeout,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Upload file data from local filesystem to AvesTerra entity

    Reads data from a local file and stores it in a file entity. Also sets
    attributions for file metadata including mode, modification time, hash,
    and version. The hash is calculated using SHA-512 for file integrity
    verification.

    Parameters
    __________
    file : AvFile
        File entity to upload data to
    path : str
        Local filesystem path to the file to upload
    version : str
        Version string to associate with the uploaded file
    timeout : AvTimeout
        Maximum time to wait for the upload operation
    authorization : AvAuthorization
        Authorization required to write to the file entity; the authorization must be present on the file adapter and the file itself

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> timeout: AvTimeout = 30.0
    >>> # Upload a local file
    >>> files.upload_file(
    ...     file=file,
    ...     path="./local_file.txt",
    ...     version="1.0.0",
    ...     timeout=timeout,
    ...     authorization=authorization
    ... )

    """
    mode = stat.S_IMODE(os.lstat(path).st_mode)

    file_mod_time = datetime.fromtimestamp(os.path.getmtime(path), tz=UTC)

    with open(path, "rb") as f:
        data = f.read()

    try:
        attributions.set_attribution(
            entity=file,
            attribute=AvAttribute.MODE,
            value=AvValue.encode_integer(mode),
            authorization=authorization,
        )
        attributions.set_attribution(
            entity=file,
            attribute=AvAttribute.TIME,
            value=AvValue.encode_time(file_mod_time),
            authorization=authorization,
        )

        
        attributions.set_attribution(
            entity=file,
            attribute=AvAttribute.HASH,
            value=AvValue.encode_string(hash_file_content(data)),
            authorization=authorization,
        )
        
        attributions.set_attribution(
            entity=file,
            attribute=AvAttribute.VERSION,
            value=AvValue.encode_string(version),
            authorization=authorization,
        )

        write_data(entity=file, data=data, timeout=timeout, authorization=authorization)
    except Exception as e:
        raise AvialError(f"Failed to upload {path} to entity {file}: {str(e)}")


def file_size(file: AvFile, authorization: AvAuthorization = NULL_AUTHORIZATION):
    """Get the size of file data stored in a file entity

    Returns the number of bytes stored in the file entity.

    Parameters
    __________
    file : AvFile
        File entity to get size from
    authorization : AvAuthorization
        Authorization required to read from the file entity; the authorization must be present on the file adapter and the file itself

    Returns
    _______
    int
        Size of file data in bytes

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> # Get file size
    >>> size = files.file_size(file=file, authorization=authorization)
    >>> print(f"File size: {size} bytes")
    """
    return AvValue.decode_integer(
        invoke_entity(file, AvMethod.COUNT, authorization=authorization)
    )


def file_time(
    file: AvFile, authorization: AvAuthorization = NULL_AUTHORIZATION
) -> AvTime:
    """Get the modification time of a file entity

    Retrieves the TIME attribution from a file entity, which represents
    the last modification time of the file when it was uploaded.

    Parameters
    __________
    file : AvFile
        File entity to get modification time from
    authorization : AvAuthorization
        Authorization required to read from the file entity

    Returns
    _______
    AvTime
        Modification time of the file

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> # Get file modification time
    >>> mod_time = files.file_time(file=file, authorization=authorization)
    >>> print(f"File last modified: {mod_time}")
    """
    return attributions.get_attribution(
        entity=file, attribute=AvAttribute.TIME, authorization=authorization
    ).decode_time()


def file_mode(file: AvFile, authorization: AvAuthorization = NULL_AUTHORIZATION):
    """Get the file mode/permissions of a file entity

    Retrieves the MODE attribution from a file entity, which represents
    the filesystem permissions of the file when it was uploaded.

    Parameters
    __________
    file : AvFile
        File entity to get mode from
    authorization : AvAuthorization
        Authorization required to read from the file entity

    Returns
    _______
    int
        File mode/permissions as an integer

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> # Get file mode
    >>> mode = files.file_mode(file=file, authorization=authorization)
    >>> print(f"File mode: {oct(mode)}")
    """
    return attributions.get_attribution(
        entity=file, attribute=AvAttribute.MODE, authorization=authorization
    ).decode_integer()


def file_hash(file: AvFile, authorization: AvAuthorization = NULL_AUTHORIZATION):
    """Get the SHA-512 hash of a file entity's data

    Retrieves the HASH attribution from a file entity, which contains
    the SHA-512 hash of the file's data for integrity verification.

    Parameters
    __________
    file : AvFile
        File entity to get hash from
    authorization : AvAuthorization
        Authorization required to read from the file entity

    Returns
    _______
    str
        SHA-512 hash of the file data as a hexadecimal string

    Examples
    ________

    >>> 
    >>> file: AvFile
    >>> authorization: AvAuthorization
    >>> # Get file hash for integrity verification
    >>> hash_value = files.file_hash(file=file, authorization=authorization)
    >>> print(f"File SHA-512 hash: {hash_value}")
    """
    return attributions.get_attribution(
        entity=file, attribute=AvAttribute.HASH, authorization=authorization
    ).decode_string()


def hash_file_content(byte_content: bytes) -> str:
    """Calculate SHA-512 hash of file content

    Computes the SHA-512 hash of the provided byte content. This is used
    internally by the upload_file function to generate hash attributions
    for file integrity verification.

    Parameters
    __________
    byte_content : bytes
        Raw byte content to hash

    Returns
    _______
    str
        SHA-512 hash as a hexadecimal string

    Examples
    ________

    >>> 
    >>> # Calculate hash of some data
    >>> data = b"Hello, World!"
    >>> hash_value = files.hash_file_content(data)
    >>> print(f"Hash: {hash_value}")
    """
    return hashlib.sha512(byte_content).hexdigest()