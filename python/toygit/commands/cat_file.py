import asyncio
import zlib
from pathlib import Path
from typing import Optional

import aiofiles

from toygit.core.git_objects import (
    BlobObject,
    CommitObject,
    GitObjectType,
    GitObjectUnion,
    TagObject,
    TreeObject,
    parse_person_info,
    parse_tree_content,
)


async def cat_file(
    object_id: str,
    repo_path: Optional[Path] = None,
    show_type: bool = False,
    show_size: bool = False,
    pretty_print: bool = False,
) -> None:
    """Show object content, type, or size."""
    if repo_path is None:
        repo_path = Path.cwd()

    git_dir = repo_path / ".git"
    if not git_dir.exists():
        raise RuntimeError(
            "fatal: not a git repository (or any of the parent directories): .git"
        )

    objects_dir = git_dir / "objects"

    # Handle full hash or abbreviated hash
    if len(object_id) < 40:
        # Find full hash from abbreviated hash
        object_id = await _resolve_abbreviated_hash(object_id, objects_dir)

    # Parse the Git object into a typed object
    git_object = await _parse_git_object(object_id, objects_dir)

    # Output based on options
    if show_type:
        print(git_object.type.value)
    elif show_size:
        print(git_object.size)
    elif pretty_print:
        print(git_object.pretty_print(), end="")
    else:
        # Default: show raw content
        content = git_object.get_content_bytes()
        # Use errors="replace" from the start to avoid double decode
        print(content.decode("utf-8", errors="replace"), end="")


async def _resolve_abbreviated_hash(abbrev_hash: str, objects_dir: Path) -> str:
    """Resolve abbreviated hash to full hash."""
    if len(abbrev_hash) < 2:
        raise RuntimeError(f"fatal: Not a valid object name {abbrev_hash}")

    # Look in the appropriate subdirectory
    obj_dir = objects_dir / abbrev_hash[:2]
    if not obj_dir.exists():
        raise RuntimeError(f"fatal: Not a valid object name {abbrev_hash}")

    # Find matching files
    remaining_hash = abbrev_hash[2:]
    matches = []

    for obj_file in obj_dir.iterdir():
        if obj_file.name.startswith(remaining_hash):
            matches.append(abbrev_hash[:2] + obj_file.name)

    if len(matches) == 0:
        raise RuntimeError(f"fatal: Not a valid object name {abbrev_hash}")
    elif len(matches) > 1:
        raise RuntimeError(
            f"fatal: ambiguous argument '{abbrev_hash}': unknown revision or path not in the working tree."
        )

    return matches[0]


async def _parse_git_object(object_id: str, objects_dir: Path) -> GitObjectUnion:
    """Parse a Git object from the object store into a typed object."""
    # Read object from objects directory
    obj_dir = objects_dir / object_id[:2]
    obj_file = obj_dir / object_id[2:]

    if not obj_file.exists():
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")

    # Read and decompress object
    async with aiofiles.open(obj_file, "rb") as f:
        compressed_data = await f.read()

    try:
        data = zlib.decompress(compressed_data)
    except zlib.error:
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")

    # Parse object header
    null_index = data.find(b"\0")
    if null_index == -1:
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")

    header = data[:null_index].decode("utf-8")
    content = data[null_index + 1 :]

    # Parse type and size from header
    parts = header.split(" ")
    if len(parts) != 2:
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")

    obj_type_str, size_str = parts
    obj_size = int(size_str)

    # Validate content size
    if len(content) != obj_size:
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")

    # Create appropriate typed object based on type
    try:
        obj_type = GitObjectType(obj_type_str)
    except ValueError:
        raise RuntimeError(f"fatal: Unknown object type {obj_type_str}")

    match obj_type:
        case GitObjectType.BLOB:
            return BlobObject(object_id=object_id, size=obj_size, content=content)
        case GitObjectType.TREE:
            entries = parse_tree_content(content)
            return TreeObject(object_id=object_id, size=obj_size, entries=entries)
        case GitObjectType.COMMIT:
            return _parse_commit_object(object_id, obj_size, content)
        case GitObjectType.TAG:
            return _parse_tag_object(object_id, obj_size, content)
        case _:
            raise RuntimeError(f"fatal: Unsupported object type {obj_type}")


def _parse_commit_object(object_id: str, size: int, content: bytes) -> CommitObject:
    """Parse commit object content."""
    lines = content.decode("utf-8").split("\n")

    tree = ""
    parents = []
    author = None
    committer = None
    message_lines = []

    in_message = False

    for line in lines:
        if in_message:
            message_lines.append(line)
        elif line == "":
            in_message = True
        elif line.startswith("tree "):
            tree = line[5:]
        elif line.startswith("parent "):
            parents.append(line[7:])
        elif line.startswith("author "):
            author = parse_person_info(line[7:])
        elif line.startswith("committer "):
            committer = parse_person_info(line[10:])

    missing_fields = []
    if not tree:
        missing_fields.append("tree")
    if not author:
        missing_fields.append("author")
    if not committer:
        missing_fields.append("committer")

    if missing_fields:
        fields_str = ", ".join(missing_fields)
        raise RuntimeError(
            f"fatal: Invalid commit object {object_id}: missing required fields: {fields_str}"
        )

    message = "\n".join(message_lines)

    # Type assertions after validation - we know these are not None due to the checks above
    assert author is not None
    assert committer is not None

    return CommitObject(
        object_id=object_id,
        size=size,
        tree=tree,
        parents=parents,
        author=author,
        committer=committer,
        message=message,
    )


def _parse_tag_object(object_id: str, size: int, content: bytes) -> TagObject:
    """Parse tag object content."""
    lines = content.decode("utf-8").split("\n")

    object_ref = ""
    object_type = None
    tag_name = ""
    tagger = None
    message_lines = []

    in_message = False

    for line in lines:
        if in_message:
            message_lines.append(line)
        elif line == "":
            in_message = True
        elif line.startswith("object "):
            object_ref = line[7:]
        elif line.startswith("type "):
            try:
                object_type = GitObjectType(line[5:])
            except ValueError:
                raise RuntimeError(f"fatal: Invalid object type in tag {object_id}")
        elif line.startswith("tag "):
            tag_name = line[4:]
        elif line.startswith("tagger "):
            tagger = parse_person_info(line[7:])

    missing_fields = []
    if not object_ref:
        missing_fields.append("object")
    if not object_type:
        missing_fields.append("type")
    if not tag_name:
        missing_fields.append("tag")
    if not tagger:
        missing_fields.append("tagger")

    if missing_fields:
        fields_str = ", ".join(missing_fields)
        raise RuntimeError(
            f"fatal: Invalid tag object {object_id}: missing required fields: {fields_str}"
        )

    message = "\n".join(message_lines)

    # Type assertions after validation - we know these are not None due to the checks above
    assert object_type is not None
    assert tagger is not None

    return TagObject(
        object_id=object_id,
        size=size,
        object_ref=object_ref,
        object_type=object_type,
        tag_name=tag_name,
        tagger=tagger,
        message=message,
    )


def cat_file_sync(
    object_id: str,
    repo_path: Optional[Path] = None,
    show_type: bool = False,
    show_size: bool = False,
    pretty_print: bool = False,
) -> None:
    """Synchronous wrapper for cat_file."""
    asyncio.run(cat_file(object_id, repo_path, show_type, show_size, pretty_print))
