import asyncio
import zlib
from pathlib import Path
from typing import Optional

import aiofiles


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
    content = data[null_index + 1:]
    
    # Parse type and size from header
    parts = header.split(" ")
    if len(parts) != 2:
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")
    
    obj_type, size_str = parts
    obj_size = int(size_str)
    
    # Validate content size
    if len(content) != obj_size:
        raise RuntimeError(f"fatal: Not a valid object name {object_id}")
    
    # Output based on options
    if show_type:
        print(obj_type)
    elif show_size:
        print(obj_size)
    elif pretty_print:
        await _pretty_print_object(obj_type, content)
    else:
        # Default: show raw content
        print(content.decode("utf-8"), end="")


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
        raise RuntimeError(f"fatal: ambiguous argument '{abbrev_hash}': unknown revision or path not in the working tree.")
    
    return matches[0]


async def _pretty_print_object(obj_type: str, content: bytes) -> None:
    """Pretty print object content based on type."""
    if obj_type == "blob":
        # For blobs, just print the content
        try:
            print(content.decode("utf-8"), end="")
        except UnicodeDecodeError:
            # For binary files, print as hex
            print(content.hex())
    elif obj_type == "tree":
        # Parse tree format: mode<space>name<null>hash
        offset = 0
        while offset < len(content):
            # Find space separator
            space_idx = content.find(b" ", offset)
            if space_idx == -1:
                break
            
            mode = content[offset:space_idx].decode("utf-8")
            offset = space_idx + 1
            
            # Find null separator
            null_idx = content.find(b"\0", offset)
            if null_idx == -1:
                break
            
            name = content[offset:null_idx].decode("utf-8")
            offset = null_idx + 1
            
            # Read 20-byte hash
            if offset + 20 > len(content):
                break
            
            hash_bytes = content[offset:offset + 20]
            hash_str = hash_bytes.hex()
            offset += 20
            
            # Determine object type from mode
            if mode.startswith("100"):
                obj_type_str = "blob"
            elif mode == "40000":
                obj_type_str = "tree"
            elif mode == "160000":
                obj_type_str = "commit"
            else:
                obj_type_str = "blob"
            
            print(f"{mode} {obj_type_str} {hash_str}\t{name}")
    elif obj_type == "commit":
        # For commits, just print the content as text
        print(content.decode("utf-8"), end="")
    elif obj_type == "tag":
        # For tags, just print the content as text
        print(content.decode("utf-8"), end="")
    else:
        # Unknown type, print as text
        print(content.decode("utf-8"), end="")


def cat_file_sync(
    object_id: str,
    repo_path: Optional[Path] = None,
    show_type: bool = False,
    show_size: bool = False,
    pretty_print: bool = False,
) -> None:
    """Synchronous wrapper for cat_file."""
    asyncio.run(cat_file(object_id, repo_path, show_type, show_size, pretty_print))