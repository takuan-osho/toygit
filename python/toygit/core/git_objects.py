"""Git object models using Pydantic for type safety."""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator


class GitObjectType(StrEnum):
    """Git object types."""

    BLOB = "blob"
    TREE = "tree"
    COMMIT = "commit"
    TAG = "tag"


class GitObject(BaseModel, ABC):
    """Base class for all Git objects."""

    object_id: str = Field(..., description="SHA-1 hash of the object")
    size: int = Field(..., ge=0, description="Size of the object content in bytes")

    @property
    @abstractmethod
    def type(self) -> GitObjectType:
        """Return the Git object type."""
        pass

    @abstractmethod
    def get_content_bytes(self) -> bytes:
        """Return the raw content as bytes."""
        pass

    @abstractmethod
    def pretty_print(self) -> str:
        """Return a pretty-printed representation of the object."""
        pass


class BlobObject(GitObject):
    """Git blob object representing file content."""

    content: bytes = Field(..., description="Raw file content")

    @property
    def type(self) -> GitObjectType:
        return GitObjectType.BLOB

    def get_content_bytes(self) -> bytes:
        return self.content

    def pretty_print(self) -> str:
        """Pretty print blob content."""
        try:
            return self.content.decode("utf-8")
        except UnicodeDecodeError:
            # For binary files, return hex representation
            return self.content.hex()

    @field_validator("size")
    @classmethod
    def validate_size(cls, v, info):
        """Validate that size matches content length."""
        if info.context is not None and "content" in info.context:
            content_len = len(info.context["content"])
            if content_len != v:
                raise ValueError(f"Size {v} doesn't match content length {content_len}")
        return v


class TreeEntry(BaseModel):
    """Entry in a tree object."""

    mode: str = Field(
        ..., pattern=r"^(100644|100755|040000|160000|120000)$", description="File mode"
    )
    name: str = Field(..., min_length=1, description="File/directory name")
    object_id: str = Field(
        ..., pattern=r"^[a-f0-9]{40}$", description="SHA-1 hash of the object"
    )

    @property
    def object_type(self) -> GitObjectType:
        """Determine object type from mode."""
        if self.mode.startswith("100"):
            return GitObjectType.BLOB
        elif self.mode == "040000":
            return GitObjectType.TREE
        elif self.mode == "160000":
            return GitObjectType.COMMIT  # Submodule
        else:
            return GitObjectType.BLOB  # Default fallback


class TreeObject(GitObject):
    """Git tree object representing directory structure."""

    entries: list[TreeEntry] = Field(default_factory=list, description="Tree entries")

    @property
    def type(self) -> GitObjectType:
        return GitObjectType.TREE

    def get_content_bytes(self) -> bytes:
        """Serialize tree entries to git format."""
        chunks = []
        for entry in sorted(self.entries, key=lambda e: e.name):
            chunks.append(f"{entry.mode} {entry.name}\0".encode("utf-8"))
            chunks.append(bytes.fromhex(entry.object_id))
        return b"".join(chunks)

    def pretty_print(self) -> str:
        """Pretty print tree content."""
        lines = []
        for entry in sorted(self.entries, key=lambda e: e.name):
            obj_type = entry.object_type.value
            lines.append(f"{entry.mode} {obj_type} {entry.object_id}\t{entry.name}")
        return "\n".join(lines)

    @field_validator("size")
    @classmethod
    def validate_size(cls, v, info):
        """Validate that size matches serialized content length."""
        if info.context is not None and "entries" in info.context:
            entries = info.context["entries"]
            content_size = sum(
                len(f"{entry.mode} {entry.name}\0".encode("utf-8")) + 20
                for entry in entries
                if hasattr(entry, "mode") and hasattr(entry, "name")
            )
            if content_size != v:
                raise ValueError(
                    f"Size {v} doesn't match content length {content_size}"
                )
        return v


class PersonInfo(BaseModel):
    """Person information for commits and tags."""

    name: str = Field(..., min_length=1, max_length=255, description="Person's name")
    email: EmailStr = Field(..., description="Person's email address")
    timestamp: datetime = Field(..., description="Commit/tag timestamp")
    timezone_offset: str = Field(
        default="+0000",
        pattern=r"^[+-]\d{4}$",
        description="Timezone offset in format +/-HHMM",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate person name doesn't contain invalid characters."""
        if "\n" in v or "\r" in v:
            raise ValueError("Name cannot contain newline characters")
        if "<" in v or ">" in v:
            raise ValueError("Name cannot contain angle brackets")
        return v.strip()

    @field_validator("timezone_offset")
    @classmethod
    def validate_timezone_offset(cls, v: str) -> str:
        """Validate timezone offset format and range."""
        if not re.match(r"^[+-]\d{4}$", v):
            raise ValueError("Timezone offset must be in format +/-HHMM")

        # Extract hours and minutes
        hours = int(v[1:3])
        minutes = int(v[3:5])

        # Validate range
        if hours > 14 or (hours == 14 and minutes > 0):
            raise ValueError("Timezone offset hours cannot exceed +/-14:00")
        if minutes >= 60:
            raise ValueError("Timezone offset minutes must be less than 60")

        return v

    @computed_field
    def timezone_info(self) -> str:
        """Get timezone info string in ISO format."""
        # Convert +/-HHMM to ISO format like +/-HH:MM
        return f"{self.timezone_offset[:3]}:{self.timezone_offset[3:]}"

    def __str__(self) -> str:
        """Format as Git person string: 'Name <email> timestamp timezone'."""
        timestamp_str = str(int(self.timestamp.timestamp()))
        return f"{self.name} <{self.email}> {timestamp_str} {self.timezone_offset}"


class CommitObject(GitObject):
    """Git commit object."""

    tree: str = Field(..., pattern=r"^[a-f0-9]{40}$", description="Tree SHA-1")
    parents: list[str] = Field(default_factory=list, description="Parent commit SHA-1s")
    author: PersonInfo = Field(..., description="Commit author")
    committer: PersonInfo = Field(..., description="Commit committer")
    message: str = Field(..., description="Commit message")

    @property
    def type(self) -> GitObjectType:
        return GitObjectType.COMMIT

    def get_content_bytes(self) -> bytes:
        """Serialize commit to git format."""
        lines = [f"tree {self.tree}"]

        for parent in self.parents:
            lines.append(f"parent {parent}")

        lines.append(f"author {self.author}")
        lines.append(f"committer {self.committer}")
        lines.append("")  # Empty line before message
        lines.append(self.message)

        return "\n".join(lines).encode("utf-8")

    def pretty_print(self) -> str:
        """Pretty print commit content."""
        return self.get_content_bytes().decode("utf-8")


class TagObject(GitObject):
    """Git tag object."""

    object_ref: str = Field(
        ..., pattern=r"^[a-f0-9]{40}$", description="Referenced object SHA-1"
    )
    object_type: GitObjectType = Field(..., description="Type of referenced object")
    tag_name: str = Field(..., min_length=1, description="Tag name")
    tagger: PersonInfo = Field(..., description="Tag creator")
    message: str = Field(..., description="Tag message")

    @property
    def type(self) -> GitObjectType:
        return GitObjectType.TAG

    def get_content_bytes(self) -> bytes:
        """Serialize tag to git format."""
        lines = [
            f"object {self.object_ref}",
            f"type {self.object_type.value}",
            f"tag {self.tag_name}",
            f"tagger {self.tagger}",
            "",  # Empty line before message
            self.message,
        ]
        return "\n".join(lines).encode("utf-8")

    def pretty_print(self) -> str:
        """Pretty print tag content."""
        return self.get_content_bytes().decode("utf-8")


# Union type for all Git objects
GitObjectUnion = BlobObject | TreeObject | CommitObject | TagObject


def parse_tree_content(content: bytes) -> list[TreeEntry]:
    """Parse tree content bytes into TreeEntry objects."""
    entries = []
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

        hash_bytes = content[offset : offset + 20]
        object_id = hash_bytes.hex()
        offset += 20

        entries.append(TreeEntry(mode=mode, name=name, object_id=object_id))

    return entries


def parse_person_info(person_str: str) -> PersonInfo:
    """Parse person info string into PersonInfo object."""
    # Format: "Name <email> timestamp timezone"
    # Example: "John Doe <john@example.com> 1234567890 +0900"

    # Find email boundaries
    email_start = person_str.rfind(" <")
    email_end = person_str.rfind("> ")

    if email_start == -1 or email_end == -1:
        raise ValueError(f"Invalid person info format: {person_str}")

    name = person_str[:email_start]
    email = person_str[email_start + 2 : email_end]

    # Parse timestamp and timezone
    remaining = person_str[email_end + 2 :].split()
    if len(remaining) != 2:
        raise ValueError(f"Invalid timestamp/timezone format: {person_str}")

    timestamp = datetime.fromtimestamp(int(remaining[0]))

    return PersonInfo(
        name=name, email=email, timestamp=timestamp, timezone_offset=remaining[1]
    )
