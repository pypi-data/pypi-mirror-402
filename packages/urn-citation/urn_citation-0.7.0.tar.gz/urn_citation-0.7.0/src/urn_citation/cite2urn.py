from pydantic import model_validator
from .urn import Urn

# Example CITE2URN
#urn:cite2:hmt:datamodels.v1:codexmodel


class Cite2Urn(Urn):
    """
    A class representing a CITE2URN, which is a specific type of URN used in the CITE architecture.
    """
    namespace: str
    collection: str
    version: str | None = None
    object_id: str | None = None

    @model_validator(mode='after')
    def validate_subreferences(self):
        """Validate subreferences in object identifier.
        
        Ensures that:
        - object_id component has at most one @ per range part
        - subreferences are not empty
        
        Raises:
            ValueError: If the subreference constraints are violated.
        """
        if self.object_id is not None:
            range_parts = self.object_id.split("-")
            for part in range_parts:
                if part.count("@") > 1:
                    raise ValueError(f"Each object component can have at most one @ delimiter for subreference, found {part.count('@')} in '{part}'")
                # Check for empty subreferences
                if "@" in part:
                    subref_parts = part.split("@")
                    if len(subref_parts) != 2 or not subref_parts[1]:
                        raise ValueError(f"Subreference cannot be empty, found empty subreference in '{part}'")
        
        return self

    @classmethod
    def from_string(cls, raw_string: str) -> "Cite2Urn":
        """Parse a ``urn:cite2`` string into a ``Cite2Urn`` instance.

        The string must be in the form ``urn:cite2:<namespace>:<collection[.version]>:<object[-range]>``.
        """
        if not raw_string.startswith("urn:cite2:"):
            raise ValueError("CITE2 URN must start with 'urn:cite2:'")

        parts = raw_string.split(":")
        if len(parts) != 5:
            raise ValueError(
                f"CITE2 URN must have 5 colon-delimited parts, got {len(parts)} from {raw_string}."
            )

        header, urn_type, namespace, collection_info, object_info = parts

        if header != "urn":
            raise ValueError("CITE2 URN must start with 'urn'")
        if urn_type != "cite2":
            raise ValueError("CITE2 URN must include the cite2 type identifier")

        if not namespace:
            raise ValueError("Namespace component cannot be empty")
        if not collection_info:
            raise ValueError("Collection info component cannot be empty")
        if not object_info:
            raise ValueError("Object component cannot be empty")

        if collection_info.endswith("."):
            raise ValueError("Collection info cannot end with a period")
        collection_parts = collection_info.split(".")
        if len(collection_parts) > 2:
            raise ValueError("Collection info can contain at most one period to separate collection and version")
        if any(part == "" for part in collection_parts):
            raise ValueError("Collection info must contain non-empty collection/version values")

        collection = collection_parts[0]
        version = collection_parts[1] if len(collection_parts) == 2 else None

        if object_info.endswith("-"):
            raise ValueError("Object component cannot end with a hyphen")
        object_parts = object_info.split("-")
        if len(object_parts) > 2:
            raise ValueError("Object component can contain at most one hyphen to indicate a range")
        if any(part == "" for part in object_parts):
            raise ValueError("Object component must contain non-empty identifiers")

        # Validate subreferences (at most one @ per range part, no empty subreferences)
        for part in object_parts:
            if part.count("@") > 1:
                raise ValueError(f"Each object component can have at most one @ delimiter for subreference, found {part.count('@')} in '{part}'")
            # Check for empty subreferences
            if "@" in part:
                subref_parts = part.split("@")
                if len(subref_parts) != 2 or not subref_parts[1]:
                    raise ValueError(f"Subreference cannot be empty, found empty subreference in '{part}'")

        object_id = object_info

        return cls(
            urn_type=urn_type,
            namespace=namespace,
            collection=collection,
            version=version,
            object_id=object_id,
        )

    def __str__(self) -> str:
        """Serialize the Cite2Urn to its canonical string form."""
        collection_part = self.collection
        if self.version is not None:
            collection_part = f"{collection_part}.{self.version}"

        object_part = self.object_id or ""

        return f"urn:{self.urn_type}:{self.namespace}:{collection_part}:{object_part}"

    def is_range(self) -> bool:
        """Return True when the object component encodes a range (single hyphen)."""
        if self.object_id is None:
            return False

        range_parts = self.object_id.split("-")
        return len(range_parts) == 2

    def range_begin(self) -> str | None:
        """Return the first identifier when the object component is a range."""
        if not self.is_range():
            return None
        return self.object_id.split("-")[0]

    def range_end(self) -> str | None:
        """Return the second identifier when the object component is a range."""
        if not self.is_range():
            return None
        return self.object_id.split("-")[1]

    def has_subreference(self) -> bool:
        """Check if the object identifier has a subreference.
        
        An object identifier has a subreference if it contains at least one @ character,
        which may appear on either or both parts of a range reference, or on
        a single reference.
        
        Returns:
            bool: True if the object identifier contains a subreference (@ character), False otherwise.
        """
        if self.object_id is None:
            return False
        
        return "@" in self.object_id

    def has_subreference1(self) -> bool:
        """Check if the range begin part has a subreference.
        
        Returns True if the URN is a range and the range begin part contains
        a @ character indicating a subreference.
        
        Returns:
            bool: True if the range begin part has a subreference, False otherwise.
        
        Raises:
            ValueError: If the URN is not a range.
        """
        if not self.is_range():
            raise ValueError("has_subreference1 can only be called on range URNs")
        
        range_begin = self.range_begin()
        return "@" in range_begin if range_begin else False

    def has_subreference2(self) -> bool:
        """Check if the range end part has a subreference.
        
        Returns True if the URN is a range and the range end part contains
        a @ character indicating a subreference.
        
        Returns:
            bool: True if the range end part has a subreference, False otherwise.
        
        Raises:
            ValueError: If the URN is not a range.
        """
        if not self.is_range():
            raise ValueError("has_subreference2 can only be called on range URNs")
        
        range_end = self.range_end()
        return "@" in range_end if range_end else False

    def subreference(self) -> str | None:
        """Get the subreference part of an object identifier.
        
        Returns the subreference part (the text after @) if the object identifier has a subreference.
        Returns None if the object identifier has no subreference.
        
        Returns:
            str | None: The subreference part, or None if no subreference exists.
        
        Raises:
            ValueError: If the URN is a range reference.
        """
        if self.is_range():
            raise ValueError("subreference can only be called on non-range URNs")
        
        if self.object_id is None or "@" not in self.object_id:
            return None
        
        parts = self.object_id.split("@")
        return parts[1]

    def subreference1(self) -> str | None:
        """Get the subreference part of the range begin reference.
        
        Returns the subreference part (the text after @) of the range begin part
        if it has a subreference. Returns None if the range begin part has no subreference.
        
        Returns:
            str | None: The subreference part of the range begin, or None if no subreference exists.
        
        Raises:
            ValueError: If the URN is not a range reference.
        """
        if not self.is_range():
            raise ValueError("subreference1 can only be called on range URNs")
        
        range_begin = self.range_begin()
        if range_begin is None or "@" not in range_begin:
            return None
        
        parts = range_begin.split("@")
        return parts[1]

    def subreference2(self) -> str | None:
        """Get the subreference part of the range end reference.
        
        Returns the subreference part (the text after @) of the range end part
        if it has a subreference. Returns None if the range end part has no subreference.
        
        Returns:
            str | None: The subreference part of the range end, or None if no subreference exists.
        
        Raises:
            ValueError: If the URN is not a range reference.
        """
        if not self.is_range():
            raise ValueError("subreference2 can only be called on range URNs")
        
        range_end = self.range_end()
        if range_end is None or "@" not in range_end:
            return None
        
        parts = range_end.split("@")
        return parts[1]

    @classmethod
    def valid_string(cls, raw_string: str) -> bool:
        """Return True when the string can be parsed into a Cite2Urn."""
        try:
            if not raw_string.startswith("urn:cite2:"):
                return False

            parts = raw_string.split(":")
            if len(parts) != 5:
                return False

            header, urn_type, namespace, collection_info, object_info = parts

            if header != "urn" or urn_type != "cite2":
                return False
            if not namespace:
                return False
            if not collection_info or not object_info:
                return False

            # Collection rules: at most one period, not ending with a period, non-empty segments
            if collection_info.endswith("."):
                return False
            collection_parts = collection_info.split(".")
            if len(collection_parts) > 2:
                return False
            if any(part == "" for part in collection_parts):
                return False

            # Object rules: at most one hyphen, not ending with hyphen, non-empty segments
            if object_info.endswith("-"):
                return False
            object_parts = object_info.split("-")
            if len(object_parts) > 2:
                return False
            if any(part == "" for part in object_parts):
                return False

            return True
        except Exception:
            return False
    def collection_equals(self, other: "Cite2Urn") -> bool:
        """Check if the collection hierarchy equals another Cite2Urn.
        
        Compares the namespace, collection, and version fields.
        
        Args:
            other (Cite2Urn): The Cite2Urn to compare with.
        
        Returns:
            bool: True if all collection hierarchy fields are equal, False otherwise.
        """
        return (
            self.namespace == other.namespace
            and self.collection == other.collection
            and self.version == other.version
        )

    def collection_contains(self, other: "Cite2Urn") -> bool:
        """Check if the collection hierarchy contains another Cite2Urn.
        
        Returns True if all non-None values of namespace, collection, and version
        in this Cite2Urn equal the corresponding values in the other Cite2Urn.
        
        Args:
            other (Cite2Urn): The Cite2Urn to compare with.
        
        Returns:
            bool: True if all non-None collection hierarchy fields match, False otherwise.
        """
        if self.namespace is not None and self.namespace != other.namespace:
            return False
        if self.collection is not None and self.collection != other.collection:
            return False
        if self.version is not None and self.version != other.version:
            return False
        return True

    def object_equals(self, other: "Cite2Urn") -> bool:
        """Check if the object identifier equals another Cite2Urn.
        
        Compares the object_id field of this Cite2Urn with the object_id field of another.
        
        Args:
            other (Cite2Urn): The Cite2Urn to compare with.
        
        Returns:
            bool: True if the object_id fields are equal, False otherwise.
        """
        return self.object_id == other.object_id

    def contains(self, other: Cite2Urn) -> bool:
        """Check if this Cite2Urn contains another Cite2Urn.
        
        Returns True if the collection hierarchy contains the other's collection hierarchy
        AND the object identifiers are exactly equal.
        
        Args:
            other (Cite2Urn): The Cite2Urn to compare with.
        
        Returns:
            bool: True if collection_contains and object_equals are both True, False otherwise.
        """
        return self.collection_contains(other) and self.object_equals(other)

    def drop_version(self) -> "Cite2Urn":
        """Create a new Cite2Urn without the version component.
        
        Returns a new Cite2Urn instance with the same collection and object
        but with the version set to None.
        
        Returns:
            Cite2Urn: A new Cite2Urn instance without the version component.
        """
        return Cite2Urn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            collection=self.collection,
            version=None,
            object_id=self.object_id,
        )

    def drop_objectid(self) -> "Cite2Urn":
        """Create a new Cite2Urn without the object_id component.
        
        Returns a new Cite2Urn instance with the same collection hierarchy
        but with the object_id set to None.
        
        Returns:
            Cite2Urn: A new Cite2Urn instance without the object_id component.
        """
        return Cite2Urn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            collection=self.collection,
            version=self.version,
            object_id=None,
        )

    def drop_subreference(self) -> "Cite2Urn":
        """Create a new Cite2Urn with all subreferences removed.
        
        Returns a new Cite2Urn instance with subreferences (text after @) removed
        from the object_id component. Works on both single objects and ranges.
        If there are no subreferences, returns a new instance with the same object_id.
        
        Returns:
            Cite2Urn: A new Cite2Urn instance without subreferences in the object_id.
        """
        if self.object_id is None or "@" not in self.object_id:
            # No subreference to drop, return copy with same object_id
            return Cite2Urn(
                urn_type=self.urn_type,
                namespace=self.namespace,
                collection=self.collection,
                version=self.version,
                object_id=self.object_id,
            )
        
        # Remove subreferences from object_id
        range_parts = self.object_id.split("-")
        cleaned_parts = []
        for part in range_parts:
            if "@" in part:
                # Keep only the part before @
                cleaned_parts.append(part.split("@")[0])
            else:
                cleaned_parts.append(part)
        
        new_object_id = "-".join(cleaned_parts)
        
        return Cite2Urn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            collection=self.collection,
            version=self.version,
            object_id=new_object_id,
        )
