import asyncio
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional

import aiofiles


async def _load_index(index_file: Path) -> dict[str, str]:
    """Load existing index from file."""
    index = {}
    if not index_file.exists():
        return index

    async with aiofiles.open(index_file, "r") as f:
        async for line in f:
            if line.strip():
                path, blob_hash = line.strip().split(" ", 1)
                index[path] = blob_hash
    return index


async def _save_index(index: dict[str, str], index_file: Path) -> None:
    """Save index to file."""
    async with aiofiles.open(index_file, "w") as f:
        for path in sorted(index.keys()):
            await f.write(f"{path} {index[path]}\n")


async def _collect_files_to_add(files: list[str], repo_path: Path) -> list[str]:
    """Collect all files that need to be added, expanding directories."""
    files_to_add = []

    async def process_file(file_path: str) -> list[str]:
        full_path = repo_path / file_path
        collected = []

        if not full_path.exists():
            print(f"fatal: pathspec '{file_path}' did not match any files")
            return collected

        if full_path.is_dir():
            for sub_file in full_path.rglob("*"):
                if sub_file.is_file() and not _is_ignored(sub_file, repo_path):
                    rel_path = sub_file.relative_to(repo_path)
                    collected.append(str(rel_path))
        else:
            if not _is_ignored(full_path, repo_path):
                collected.append(file_path)

        return collected

    # Process files concurrently
    tasks = [process_file(file_path) for file_path in files]
    results = await asyncio.gather(*tasks)

    for file_list in results:
        files_to_add.extend(file_list)

    return files_to_add


async def add_files(files: list[str], repo_path: Optional[Path] = None) -> None:
    """Add files to the staging area."""
    if repo_path is None:
        repo_path = Path.cwd()

    git_dir = repo_path / ".git"
    if not git_dir.exists():
        raise RuntimeError(
            "fatal: not a git repository (or any of the parent directories): .git"
        )

    objects_dir = git_dir / "objects"
    index_file = git_dir / "index"

    index = await _load_index(index_file)
    files_to_add = await _collect_files_to_add(files, repo_path)

    # Process files concurrently in batches to avoid overwhelming the system
    semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
    index_lock = asyncio.Lock()  # Protect index modifications from race conditions

    async def process_with_semaphore(file_path: str, repo: Path):
        async with semaphore:
            await _add_single_file(file_path, repo, objects_dir, index, index_lock)

    tasks = [process_with_semaphore(file_path, repo_path) for file_path in files_to_add]
    await asyncio.gather(*tasks)
    await _save_index(index, index_file)


async def _add_single_file(
    file_path: str,
    repo_path: Path,
    objects_dir: Path,
    index: dict,
    index_lock: asyncio.Lock,
) -> None:
    """Add a single file to the staging area."""
    full_path = repo_path / file_path

    # Read file content with comprehensive error handling
    try:
        async with aiofiles.open(full_path, "rb") as f:
            content = await f.read()
    except FileNotFoundError:
        print(
            f"error: unable to read file '{file_path}': [Errno 2] No such file or directory"
        )
        return
    except PermissionError:
        print(f"error: insufficient permission to read '{file_path}'")
        return
    except IsADirectoryError:
        print(f"error: '{file_path}' is a directory")
        return
    except (OSError, IOError) as e:
        print(f"error: unable to read file '{file_path}': {e}")
        return
    except Exception as e:
        print(f"error: unexpected error reading file '{file_path}': {e}")
        return

    # Create blob object
    blob_data = b"blob " + str(len(content)).encode() + b"\0" + content
    blob_hash = hashlib.sha1(blob_data).hexdigest()

    # Store blob object with atomic write to prevent race conditions
    obj_dir = objects_dir / blob_hash[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj_file = obj_dir / blob_hash[2:]

    if not obj_file.exists():
        # Use atomic write to prevent race conditions
        temp_fd, temp_path = tempfile.mkstemp(dir=obj_dir)
        try:
            os.close(temp_fd)  # Close file descriptor since we'll use aiofiles
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(blob_data)
            # Atomic move - this prevents corruption from concurrent writes
            os.rename(temp_path, obj_file)
        except Exception:
            # Clean up temp file if something goes wrong
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    # Update index with thread-safe locking
    async with index_lock:
        index[file_path] = blob_hash
    print(f"add '{file_path}'")


def _is_ignored(file_path: Path, repo_path: Path) -> bool:
    """Check if file should be ignored."""
    # Always ignore .git directory
    try:
        rel_path = file_path.relative_to(repo_path)
        if ".git" in rel_path.parts:
            return True
    except ValueError:
        # file_path is not relative to repo_path
        pass

    return False


def add_files_sync(files: list[str], repo_path: Optional[Path] = None) -> None:
    """Synchronous wrapper for add_files."""
    asyncio.run(add_files(files, repo_path))
