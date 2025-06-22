import hashlib
from pathlib import Path
from typing import Optional


def _load_index(index_file: Path) -> dict[str, str]:
    """Load existing index from file."""
    index = {}
    if not index_file.exists():
        return index

    with open(index_file, "r") as f:
        for line in f:
            if line.strip():
                path, blob_hash = line.strip().split(" ", 1)
                index[path] = blob_hash
    return index


def _save_index(index: dict[str, str], index_file: Path) -> None:
    """Save index to file."""
    with open(index_file, "w") as f:
        for path in sorted(index.keys()):
            f.write(f"{path} {index[path]}\n")


def _collect_files_to_add(files: list[str], repo_path: Path) -> list[str]:
    """Collect all files that need to be added, expanding directories."""
    files_to_add = []

    for file_path in files:
        full_path = repo_path / file_path

        if not full_path.exists():
            print(f"fatal: pathspec '{file_path}' did not match any files")
            continue

        if full_path.is_dir():
            for sub_file in full_path.rglob("*"):
                if sub_file.is_file() and not _is_ignored(sub_file, repo_path):
                    rel_path = sub_file.relative_to(repo_path)
                    files_to_add.append(str(rel_path))
        else:
            if not _is_ignored(full_path, repo_path):
                files_to_add.append(file_path)

    return files_to_add


def add_files(files: list[str], repo_path: Optional[Path] = None) -> None:
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

    index = _load_index(index_file)
    files_to_add = _collect_files_to_add(files, repo_path)

    for file_path in files_to_add:
        _add_single_file(file_path, repo_path, objects_dir, index)

    _save_index(index, index_file)


def _add_single_file(
    file_path: str, repo_path: Path, objects_dir: Path, index: dict
) -> None:
    """Add a single file to the staging area."""
    full_path = repo_path / file_path

    # Read file content
    try:
        with open(full_path, "rb") as f:
            content = f.read()
    except Exception as e:
        print(f"error: unable to read file '{file_path}': {e}")
        return

    # Create blob object
    blob_data = b"blob " + str(len(content)).encode() + b"\0" + content
    blob_hash = hashlib.sha1(blob_data).hexdigest()

    # Store blob object
    obj_dir = objects_dir / blob_hash[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj_file = obj_dir / blob_hash[2:]

    if not obj_file.exists():
        with open(obj_file, "wb") as f:
            f.write(blob_data)

    # Update index
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
