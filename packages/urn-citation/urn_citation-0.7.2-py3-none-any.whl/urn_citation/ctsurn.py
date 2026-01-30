from pydantic import model_validator
from .urn import Urn
    
class CtsUrn(Urn):
    """A CTS URN identifying a passage of a canonically citable text.

    Canonical Text Service (CTS) URNs model passages of texts with two overlapping hierarchies: a work hierarchy, and a passage hierarchy. Values in the work hierarchy belong to a specified namespace. The work hierarchy is required to identify at least a text group; optionally, it may specify a work, a version (edition or translation) of the work, and exemplar (specific copy of the version). The passage hierarchy may be empty, in which case the URN refers to the entire contents of the work identified in the work hierarchy. Otherwise, the passage hierarchy identifies a specific passage of the work, at any depth of the citation hierarchy appropriate for the work (e.g., book, chapter, verse, line, token.) The passage hierarchy may identify either a single passage or a range of passages.

    Attributes:
        namespace (str): Required identifier for the namespace of the text (e.g., "greekLit" or "latinLit") where values for the work hierarchy are defined.
        text_group (str): Required identifier for text group.
        work (str): Optional identifier for work.
        version (str): Optional identifier for version (edition or translation) of the work.
        exemplar (str): Optional identifier for exemplar (specific copy of the version) of the work.
        passage (str): Optional identifier for passage of the work, at any depth of the citation hierarchy appropriate for the work (e.g., book, chapter, verse, line, token). May identify either a single passage or a range of passages.
    """    
    namespace: str
    text_group: str
    work: str | None = None
    version: str | None = None
    exemplar: str | None = None
    passage: str | None = None

    @model_validator(mode='after')
    def validate_work_hierarchy(self):
        """Validate the work hierarchy structure.
        
        Ensures that:
        - version cannot be set if work is None
        - exemplar cannot be set if version or work is None
        - passage component has at most one @ per range part
        
        Raises:
            ValueError: If the hierarchy constraints are violated.
        """
        if self.version is not None and self.work is None:
            raise ValueError("version cannot be set when work is None")
        
        # Check work before version for exemplar (check hierarchy from root to leaf)
        if self.exemplar is not None and self.work is None:
            raise ValueError("exemplar cannot be set when work is None")
        
        if self.exemplar is not None and self.version is None:
            raise ValueError("exemplar cannot be set when version is None")
        
        # Validate subreferences in passage component
        if self.passage is not None:
            range_parts = self.passage.split("-")
            for part in range_parts:
                if part.count("@") > 1:
                    raise ValueError(f"Each passage component can have at most one @ delimiter for subreference, found {part.count('@')} in '{part}'")
                # Check for empty subreferences
                if "@" in part:
                    subref_parts = part.split("@")
                    if len(subref_parts) != 2 or not subref_parts[1]:
                        raise ValueError(f"Subreference cannot be empty, found empty subreference in '{part}'")
        
        return self

    @classmethod
    def from_string(cls, raw_string):
        # 1. Split the string into a list of values
        parts = raw_string.split(":")
        if len(parts) != 5:
            raise ValueError("Bad.")
        header, urn_type, namespace, work_component, passage_component = parts

        rangeparts = passage_component.split("-")
        if len(rangeparts) > 2:
            raise ValueError(f"Passage component of CTS URN cannot have more than one hyphen to indicate a range, found {len(rangeparts)-1} hyphenated parts in {passage_component}.")
        
        # Validate subreferences (at most one @ per range part)
        for part in rangeparts:
            if part.count("@") > 1:
                raise ValueError(f"Each passage component can have at most one @ delimiter for subreference, found {part.count('@')} in '{part}'")
            # Check for empty subreferences
            if "@" in part:
                subref_parts = part.split("@")
                if len(subref_parts) != 2 or not subref_parts[1]:
                    raise ValueError(f"Subreference cannot be empty, found empty subreference in '{part}'")
        
        if ".." in work_component:
            raise ValueError(f"Work component of CTS URN cannot contain successive periods, found in {work_component}.")
        
        if ".." in passage_component:
            raise ValueError(f"Passage component of CTS URN cannot contain successive periods, found in {passage_component}.")
        
        workparts = work_component.split(".")
        if len(workparts) > 4:
            raise ValueError(f"Work component of CTS URN cannot have more than 4 dot-delimited components, got {len(workparts)} from {work_component}.")

        groupid, workid, versionid, exemplarid =         (workparts + [None] * 4)[:4]
     
        if not passage_component:
            passage_component = None

        return cls(
            urn_type=urn_type,
            namespace=namespace,
            text_group=groupid,
            work=workid,
            version=versionid,
            exemplar=exemplarid,
            passage=passage_component
        )

    def __str__(self) -> str:
        """Serialize the CtsUrn to its string representation.
        
        Returns a CTS URN string in the format:
        urn:cts:namespace:work.hierarchy:passage
        
        Where work.hierarchy is constructed from the text_group, work, version, and exemplar,
        and passage is the passage component (or empty string if None).
        
        Returns:
            str: The serialized CTS URN string.
        """
        # Build the work component from the work hierarchy
        work_parts = [self.text_group]
        if self.work is not None:
            work_parts.append(self.work)
        if self.version is not None:
            work_parts.append(self.version)
        if self.exemplar is not None:
            work_parts.append(self.exemplar)
        
        work_component = ".".join(work_parts)
        
        # Build the passage component (empty string if None)
        passage_component = self.passage if self.passage is not None else ""
        
        # Construct the full URN string
        return f"urn:{self.urn_type}:{self.namespace}:{work_component}:{passage_component}"

    def is_range(self) -> bool:
        """Check if the passage component represents a range.
        
        A passage is a range if it contains exactly one hyphen, indicating both
        a range beginning and range end separated by that hyphen.
        
        Returns:
            bool: True if the passage is a range, False otherwise.
        """
        if self.passage is None:
            return False
        
        range_parts = self.passage.split("-")
        return len(range_parts) == 2

    def has_subreference(self) -> bool:
        """Check if the passage component has a subreference.
        
        A passage has a subreference if it contains at least one @ character,
        which may appear on either or both parts of a range reference, or on
        a single reference.
        
        Returns:
            bool: True if the passage contains a subreference (@ character), False otherwise.
        """
        if self.passage is None:
            return False
        
        return "@" in self.passage

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
        """Get the subreference part of a passage reference.
        
        Returns the subreference part (the text after @) if the passage has a subreference.
        Returns None if the passage has no subreference.
        
        Returns:
            str | None: The subreference part, or None if no subreference exists.
        
        Raises:
            ValueError: If the URN is a range reference.
        """
        if self.is_range():
            raise ValueError("subreference can only be called on non-range URNs")
        
        if self.passage is None or "@" not in self.passage:
            return None
        
        parts = self.passage.split("@")
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

    def range_begin(self) -> str | None:
        """Get the beginning of a passage range.
        
        Returns the first range piece if the passage component represents a range
        (i.e., contains exactly one hyphen). Returns None if the passage is not
        a range or if passage is None.
        
        Returns:
            str | None: The beginning of the range, or None if not a range.
        """
        if not self.is_range():
            return None
        
        range_parts = self.passage.split("-")
        return range_parts[0]

    def range_end(self) -> str | None:
        """Get the end of a passage range.
        
        Returns the second range piece if the passage component represents a range
        (i.e., contains exactly one hyphen). Returns None if the passage is not
        a range or if passage is None.
        
        Returns:
            str | None: The end of the range, or None if not a range.
        """
        if not self.is_range():
            return None
        
        range_parts = self.passage.split("-")
        return range_parts[1]

    @classmethod
    def valid_string(cls, raw_string: str) -> bool:
        """Check if a string is valid for constructing a CtsUrn.
        
        A valid CTS URN string must:
        - Split into exactly 5 colon-delimited components
        - Have a passage component with at most 1 hyphen (for ranges)
        - Have a work component with at most 4 dot-delimited parts
        
        Args:
            raw_string (str): The string to validate.
        
        Returns:
            bool: True if the string is valid, False otherwise.
        """
        try:
            parts = raw_string.split(":")
            if len(parts) != 5:
                return False
            
            header, urn_type, namespace, work_component, passage_component = parts
            
            # Check passage component (at most 1 hyphen)
            rangeparts = passage_component.split("-")
            if len(rangeparts) > 2:
                return False
            
            # Check for successive periods in work and passage components
            if ".." in work_component or ".." in passage_component:
                return False
            
            # Check work component (at most 4 dot-delimited parts)
            workparts = work_component.split(".")
            if len(workparts) > 4:
                return False
            
            return True
        except Exception:
            return False

    def work_equals(self, other: CtsUrn) -> bool:
        """Check if the work hierarchy is equal to another CtsUrn.
        
        Compares the text_group, work, version, and exemplar fields.
        
        Args:
            other (CtsUrn): The CtsUrn to compare with.
        
        Returns:
            bool: True if all work hierarchy fields are equal, False otherwise.
        """
        return (
            self.text_group == other.text_group
            and self.work == other.work
            and self.version == other.version
            and self.exemplar == other.exemplar
        )


    # rewrite this using a more elegant `getattr` approach, and also add a docstring
    def work_contains(self, other: CtsUrn) -> bool:
        """Check if the work hierarchy contains another CtsUrn.
        
        Returns True if all non-None values of text_group, work, version, and exemplar
        in this CtsUrn equal the corresponding values in the other CtsUrn.
        
        Args:
            other (CtsUrn): The CtsUrn to compare with.
        
        Returns:
            bool: True if all non-None work hierarchy fields match, False otherwise.
        """
        if self.text_group is not None and self.text_group != other.text_group:
            return False
        if self.work is not None and self.work != other.work:
            return False
        if self.version is not None and self.version != other.version:
            return False
        if self.exemplar is not None and self.exemplar != other.exemplar:
            return False
        return True

    def passage_equals(self, other: CtsUrn) -> bool:
        """Check if the passage component is equal to another CtsUrn.
        
        Compares the passage field of this CtsUrn with the passage field of another.
        
        Args:
            other (CtsUrn): The CtsUrn to compare with.
        
        Returns:
            bool: True if the passage fields are equal, False otherwise.
        """
        return self.passage == other.passage

    def passage_contains(self, other: CtsUrn) -> bool:
        """Check if the passage component contains another CtsUrn.
        
        Returns True if:
        - The passages are exactly equal, OR
        - The other passage is at least 2 characters longer and starts with 
          this passage followed by a period character.
        
        Raises ValueError if either passage is a range.
        
        Examples:
        - passage="1", other.passage="1.11" -> True
        - passage="1", other.passage="12" -> False
        
        Args:
            other (CtsUrn): The CtsUrn to compare with.
        
        Returns:
            bool: True if the passages match the similarity criteria, False otherwise.
        
        Raises:
            ValueError: If either passage is a range (contains a hyphen).
        """
        if self.is_range():
            raise ValueError("passage_contains cannot be called on a CtsUrn with a range passage")
        if other.is_range():
            raise ValueError("passage_contains cannot be called with a CtsUrn argument that has a range passage")
        
        # Check exact equality
        if self.passage == other.passage:
            return True
        
        # Check if other passage is a refinement of this passage
        if self.passage is not None and other.passage is not None:
            expected_prefix = self.passage + "."
            return (
                len(other.passage) >= len(self.passage) + 2
                and other.passage.startswith(expected_prefix)
            )
        
        return False

    def contains(self, other: CtsUrn) -> bool:
        """Check if this CtsUrn contains another CtsUrn.
        
        Returns True if both the work hierarchy and passage contain the other.
        
        Args:
            other (CtsUrn): The CtsUrn to compare with.
        
        Returns:
            bool: True if both work_contains and passage_contains are True, False otherwise.
        """
        return self.work_contains(other) and self.passage_contains(other)
   
    def drop_passage(self) -> CtsUrn:
        """Create a new CtsUrn without the passage component.
        
        Returns a new CtsUrn instance with the same work hierarchy but
        with the passage set to None.
        
        Returns:
            CtsUrn: A new CtsUrn instance without the passage component.
        """
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=self.version,
            exemplar=self.exemplar,
            passage=None
        )
    
    def set_passage(self, new_passage: str) -> CtsUrn:
        """Create a new CtsUrn with a specified passage component.
        
        Returns a new CtsUrn instance with the same work hierarchy but
        with the passage set to the provided new_passage value.
        
        Args:
            new_passage (str | None): The new passage component to set.
        
        Returns:
            CtsUrn: A new CtsUrn instance with the updated passage component.
        """
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=self.version,
            exemplar=self.exemplar,
            passage=new_passage
        )


    def drop_subreference(self) -> CtsUrn:
        """Create a new CtsUrn with all subreferences removed.
        
        Returns a new CtsUrn instance with subreferences (text after @) removed
        from the passage component. Works on both single passages and ranges.
        If there are no subreferences, returns a new instance with the same passage.
        
        Returns:
            CtsUrn: A new CtsUrn instance without subreferences in the passage.
        """
        if self.passage is None or "@" not in self.passage:
            # No subreference to drop, return copy with same passage
            return CtsUrn(
                urn_type=self.urn_type,
                namespace=self.namespace,
                text_group=self.text_group,
                work=self.work,
                version=self.version,
                exemplar=self.exemplar,
                passage=self.passage
            )
        
        # Remove subreferences from passage
        range_parts = self.passage.split("-")
        cleaned_parts = []
        for part in range_parts:
            if "@" in part:
                # Keep only the part before @
                cleaned_parts.append(part.split("@")[0])
            else:
                cleaned_parts.append(part)
        
        new_passage = "-".join(cleaned_parts)
        
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=self.version,
            exemplar=self.exemplar,
            passage=new_passage
        )

    def drop_version(self) -> CtsUrn:
        """Create a new CtsUrn without the version component.
        
        Returns a new CtsUrn instance with the same work hierarchy but
        with the version set to None. Note: exemplar will also be set to None
        since exemplar cannot exist without a version.
        
        Returns:
            CtsUrn: A new CtsUrn instance without the version component.
        """
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=None,
            exemplar=None,  # Must also drop exemplar since it requires version
            passage=self.passage
        )
    

    def set_version(self, new_version: str) -> CtsUrn:
        """Create a new CtsUrn with a specified version component.
        
        Returns a new CtsUrn instance with the same work hierarchy but
        with the version set to the provided new_version value.
        
        Args:
            new_version (str | None): The new version component to set.
        
        Returns:
            CtsUrn: A new CtsUrn instance with the updated version component.
        """
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=new_version,
            exemplar=self.exemplar,
            passage=self.passage
        )
    
    def drop_exemplar(self) -> CtsUrn:
        """Create a new CtsUrn without the exemplar component.
        
        Returns a new CtsUrn instance with the same work hierarchy but
        with the exemplar set to None.
        
        Returns:
            CtsUrn: A new CtsUrn instance without the exemplar component.
        """
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=self.version,
            exemplar=None,
            passage=self.passage
        )
    
    def set_exemplar(self, new_exemplar: str) -> CtsUrn:
        """Create a new CtsUrn with a specified exemplar component.
        
        Returns a new CtsUrn instance with the same work hierarchy but
        with the exemplar set to the provided new_exemplar value.
        
        Args:
            new_exemplar (str | None): The new exemplar component to set.
        
        Returns:
            CtsUrn: A new CtsUrn instance with the updated exemplar component.
        """
        return CtsUrn(
            urn_type=self.urn_type,
            namespace=self.namespace,
            text_group=self.text_group,
            work=self.work,
            version=self.version,
            exemplar=new_exemplar,
            passage=self.passage
        )