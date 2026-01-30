import pytest
from pydantic import ValidationError

from urn_citation import CtsUrn


class TestCtsUrnCreation:
    """Tests for CtsUrn creation and validation."""

    def test_ctsurn_creation_with_required_fields(self):
        """Test creating a CtsUrn with required fields only."""
        urn = CtsUrn(urn_type="cts", namespace="greekLit", text_group="tlg0012")
        assert urn.urn_type == "cts"
        assert urn.namespace == "greekLit"
        assert urn.text_group == "tlg0012"
        assert urn.work is None
        assert urn.version is None
        assert urn.exemplar is None
        assert urn.passage is None

    def test_ctsurn_creation_with_all_fields(self):
        """Test creating a CtsUrn with all fields populated."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        assert urn.text_group == "tlg0012"
        assert urn.work == "001"
        assert urn.version == "wacl1"
        assert urn.exemplar == "ex1"
        assert urn.passage == "1.1"

    def test_ctsurn_requires_namespace(self):
        """Test that namespace is required."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(urn_type="cts", text_group="tlg0012")
        assert "namespace" in str(exc_info.value)

    def test_ctsurn_requires_text_group(self):
        """Test that text_group is required."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(urn_type="cts", namespace="greekLit")
        assert "text_group" in str(exc_info.value)

    def test_ctsurn_version_requires_work(self):
        """Test that version cannot be set when work is None."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                version="wacl1"
            )
        assert "version cannot be set when work is None" in str(exc_info.value)

    def test_ctsurn_exemplar_requires_work(self):
        """Test that exemplar cannot be set when work is None."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                exemplar="ex1"
            )
        assert "exemplar cannot be set when work is None" in str(exc_info.value)

    def test_ctsurn_exemplar_requires_version(self):
        """Test that exemplar cannot be set when version is None."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="001",
                exemplar="ex1"
            )
        assert "exemplar cannot be set when version is None" in str(exc_info.value)

    def test_ctsurn_with_work_only(self):
        """Test creating a CtsUrn with text_group and work only."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        assert urn.work == "001"
        assert urn.version is None
        assert urn.exemplar is None

    def test_ctsurn_with_work_and_version(self):
        """Test creating a CtsUrn with text_group, work, and version."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        assert urn.work == "001"
        assert urn.version == "wacl1"
        assert urn.exemplar is None

    def test_ctsurn_passage_independent_of_hierarchy(self):
        """Test that passage can be set regardless of work hierarchy."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn.work is None
        assert urn.passage == "1.1"


class TestCtsUrnToString:
    """Tests for the __str__ method."""

    def test_str_basic_urn(self):
        """Test serializing a basic CtsUrn with only required fields."""
        urn = CtsUrn(urn_type="cts", namespace="greekLit", text_group="tlg0012")
        assert str(urn) == "urn:cts:greekLit:tlg0012:"

    def test_str_with_work(self):
        """Test serialization of a URN with text_group and work."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        assert str(urn) == "urn:cts:greekLit:tlg0012.001:"

    def test_str_with_version(self):
        """Test serialization of a URN with text_group, work, and version."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        assert str(urn) == "urn:cts:greekLit:tlg0012.001.wacl1:"

    def test_str_with_exemplar(self):
        """Test serialization of a URN with text_group, work, version, and exemplar."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        assert str(urn) == "urn:cts:greekLit:tlg0012.001.wacl1.ex1:"

    def test_str_with_passage(self):
        """Test serialization of a URN with text_group and passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert str(urn) == "urn:cts:greekLit:tlg0012:1.1"

    def test_str_with_all_components(self):
        """Test serialization of a URN with all components including a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1-1.5"
        )
        assert str(urn) == "urn:cts:greekLit:tlg0012.001.wacl1.ex1:1.1-1.5"


class TestCtsUrnIsRange:
    """Tests for the is_range method."""

    def test_is_range_with_range_passage(self):
        """Test is_range returns True for a range passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        assert urn.is_range() is True

    def test_is_range_with_single_passage(self):
        """Test is_range returns False for a single passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn.is_range() is False

    def test_is_range_with_none_passage(self):
        """Test is_range returns False when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn.is_range() is False

    def test_is_range_with_empty_string_passage(self):
        """Test is_range returns False for empty string passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage=""
        )
        assert urn.is_range() is False


class TestCtsUrnRangeBegin:
    """Tests for the range_begin method."""

    def test_range_begin_with_range(self):
        """Test range_begin returns the first part of a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        assert urn.range_begin() == "1.1"

    def test_range_begin_with_single_passage(self):
        """Test range_begin returns None for a single passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn.range_begin() is None

    def test_range_begin_with_none_passage(self):
        """Test range_begin returns None when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn.range_begin() is None


class TestCtsUrnRangeEnd:
    """Tests for the range_end method."""

    def test_range_end_with_range(self):
        """Test range_end returns the second part of a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        assert urn.range_end() == "1.5"

    def test_range_end_with_single_passage(self):
        """Test range_end returns None for a single passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn.range_end() is None

    def test_range_end_with_none_passage(self):
        """Test range_end returns None when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn.range_end() is None


class TestCtsUrnHasSubreference:
    """Tests for the has_subreference method."""

    def test_has_subreference_single_passage_with_subreference(self):
        """Test has_subreference returns True for a single passage with subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_single_passage_without_subreference(self):
        """Test has_subreference returns False for a single passage without subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn.has_subreference() is False

    def test_has_subreference_range_with_subreference_on_both_parts(self):
        """Test has_subreference returns True when both range parts have subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.1@θεά"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_range_with_subreference_on_first_part(self):
        """Test has_subreference returns True when only first range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_range_with_subreference_on_second_part(self):
        """Test has_subreference returns True when only second range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@οὐλομένην"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_range_without_subreference(self):
        """Test has_subreference returns False for a range without any subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        assert urn.has_subreference() is False

    def test_has_subreference_none_passage(self):
        """Test has_subreference returns False when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn.has_subreference() is False

    def test_has_subreference_empty_string_passage(self):
        """Test has_subreference returns False for empty string passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage=""
        )
        assert urn.has_subreference() is False


class TestCtsUrnHasSubreference1:
    """Tests for the has_subreference1 method."""

    def test_has_subreference1_range_with_subreference_on_first_part(self):
        """Test has_subreference1 returns True when first range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2"
        )
        assert urn.has_subreference1() is True

    def test_has_subreference1_range_without_subreference_on_first_part(self):
        """Test has_subreference1 returns False when first range part lacks subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@θεά"
        )
        assert urn.has_subreference1() is False

    def test_has_subreference1_range_with_subreference_on_both_parts(self):
        """Test has_subreference1 returns True when both range parts have subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2@θεά"
        )
        assert urn.has_subreference1() is True

    def test_has_subreference1_range_without_any_subreference(self):
        """Test has_subreference1 returns False when neither range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.5"
        )
        assert urn.has_subreference1() is False

    def test_has_subreference1_raises_error_on_single_passage(self):
        """Test has_subreference1 raises ValueError when URN is not a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference1()
        assert "has_subreference1 can only be called on range URNs" in str(exc_info.value)

    def test_has_subreference1_raises_error_on_none_passage(self):
        """Test has_subreference1 raises ValueError when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference1()
        assert "has_subreference1 can only be called on range URNs" in str(exc_info.value)


class TestCtsUrnHasSubreference2:
    """Tests for the has_subreference2 method."""

    def test_has_subreference2_range_with_subreference_on_second_part(self):
        """Test has_subreference2 returns True when second range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@θεά"
        )
        assert urn.has_subreference2() is True

    def test_has_subreference2_range_without_subreference_on_second_part(self):
        """Test has_subreference2 returns False when second range part lacks subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2"
        )
        assert urn.has_subreference2() is False

    def test_has_subreference2_range_with_subreference_on_both_parts(self):
        """Test has_subreference2 returns True when both range parts have subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2@θεά"
        )
        assert urn.has_subreference2() is True

    def test_has_subreference2_range_without_any_subreference(self):
        """Test has_subreference2 returns False when neither range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.5"
        )
        assert urn.has_subreference2() is False

    def test_has_subreference2_raises_error_on_single_passage(self):
        """Test has_subreference2 raises ValueError when URN is not a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.2@θεά"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference2()
        assert "has_subreference2 can only be called on range URNs" in str(exc_info.value)

    def test_has_subreference2_raises_error_on_none_passage(self):
        """Test has_subreference2 raises ValueError when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference2()
        assert "has_subreference2 can only be called on range URNs" in str(exc_info.value)


class TestCtsUrnSubreference:
    """Tests for the subreference method."""

    def test_subreference_single_passage_with_subreference(self):
        """Test subreference returns the subreference part for a single passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν"
        )
        assert urn.subreference() == "μῆνιν"

    def test_subreference_single_passage_without_subreference(self):
        """Test subreference returns None for a single passage without subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1"
        )
        assert urn.subreference() is None

    def test_subreference_none_passage(self):
        """Test subreference returns None when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn.subreference() is None

    def test_subreference_raises_error_on_range(self):
        """Test subreference raises ValueError when URN is a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2@θεά"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference()
        assert "subreference can only be called on non-range URNs" in str(exc_info.value)

    def test_subreference_raises_error_on_range_without_subreference(self):
        """Test subreference raises ValueError for a range without subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.5"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference()
        assert "subreference can only be called on non-range URNs" in str(exc_info.value)

    def test_subreference_with_complex_subreference(self):
        """Test subreference with a complex subreference string."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@word1[2]"
        )
        assert urn.subreference() == "word1[2]"


class TestCtsUrnSubreference1:
    """Tests for the subreference1 method."""

    def test_subreference1_range_with_subreference_on_first_part(self):
        """Test subreference1 returns the subreference part of the range begin."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2"
        )
        assert urn.subreference1() == "μῆνιν"

    def test_subreference1_range_without_subreference_on_first_part(self):
        """Test subreference1 returns None when first range part lacks subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@θεά"
        )
        assert urn.subreference1() is None

    def test_subreference1_range_with_subreference_on_both_parts(self):
        """Test subreference1 returns the first subreference when both parts have subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2@θεά"
        )
        assert urn.subreference1() == "μῆνιν"

    def test_subreference1_range_without_any_subreference(self):
        """Test subreference1 returns None when neither range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.5"
        )
        assert urn.subreference1() is None

    def test_subreference1_raises_error_on_single_passage(self):
        """Test subreference1 raises ValueError when URN is not a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference1()
        assert "subreference1 can only be called on range URNs" in str(exc_info.value)

    def test_subreference1_raises_error_on_none_passage(self):
        """Test subreference1 raises ValueError when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference1()
        assert "subreference1 can only be called on range URNs" in str(exc_info.value)

    def test_subreference1_with_complex_subreference(self):
        """Test subreference1 with a complex subreference string."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@word1[2]-1.2"
        )
        assert urn.subreference1() == "word1[2]"


class TestCtsUrnSubreference2:
    """Tests for the subreference2 method."""

    def test_subreference2_range_with_subreference_on_second_part(self):
        """Test subreference2 returns the subreference part of the range end."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@θεά"
        )
        assert urn.subreference2() == "θεά"

    def test_subreference2_range_without_subreference_on_second_part(self):
        """Test subreference2 returns None when second range part lacks subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2"
        )
        assert urn.subreference2() is None

    def test_subreference2_range_with_subreference_on_both_parts(self):
        """Test subreference2 returns the second subreference when both parts have subreferences."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2@θεά"
        )
        assert urn.subreference2() == "θεά"

    def test_subreference2_range_without_any_subreference(self):
        """Test subreference2 returns None when neither range part has subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.5"
        )
        assert urn.subreference2() is None

    def test_subreference2_raises_error_on_single_passage(self):
        """Test subreference2 raises ValueError when URN is not a range."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.2@θεά"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference2()
        assert "subreference2 can only be called on range URNs" in str(exc_info.value)

    def test_subreference2_raises_error_on_none_passage(self):
        """Test subreference2 raises ValueError when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference2()
        assert "subreference2 can only be called on range URNs" in str(exc_info.value)

    def test_subreference2_with_complex_subreference(self):
        """Test subreference2 with a complex subreference string."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@word2[3]"
        )
        assert urn.subreference2() == "word2[3]"


class TestCtsUrnSubreferenceValidation:
    """Tests for subreference validation in CtsUrn."""

    def test_multiple_subreferences_in_single_passage_constructor(self):
        """Test that multiple @ signs in a single passage raise ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1@μῆνιν@θεά"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_single_passage_from_string(self):
        """Test that multiple @ signs in a single passage raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@μῆνιν@θεά")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_first_part_constructor(self):
        """Test that multiple @ signs in first range part raise ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1@μῆνιν@extra-1.2"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_first_part_from_string(self):
        """Test that multiple @ signs in first range part raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@μῆνιν@extra-1.2")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_second_part_constructor(self):
        """Test that multiple @ signs in second range part raise ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1-1.2@οὐλομένην@extra"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_second_part_from_string(self):
        """Test that multiple @ signs in second range part raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1-1.2@οὐλομένην@extra")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_both_range_parts_constructor(self):
        """Test that multiple @ signs in both range parts raise ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1@μῆνιν@extra-1.2@θεά@extra2"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_both_range_parts_from_string(self):
        """Test that multiple @ signs in both range parts raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@μῆνιν@extra-1.2@θεά@extra2")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_valid_single_subreference_single_passage(self):
        """Test that a single @ sign in a single passage is valid."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν"
        )
        assert urn.passage == "1.1@μῆνιν"
        assert urn.has_subreference() is True

    def test_valid_single_subreference_range_first_part(self):
        """Test that a single @ sign in first range part is valid."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.2"
        )
        assert urn.passage == "1.1@μῆνιν-1.2"
        assert urn.has_subreference() is True

    def test_valid_single_subreference_range_second_part(self):
        """Test that a single @ sign in second range part is valid."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1-1.2@οὐλομένην"
        )
        assert urn.passage == "1.1-1.2@οὐλομένην"
        assert urn.has_subreference() is True

    def test_valid_single_subreference_both_range_parts(self):
        """Test that one @ sign in each range part is valid."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="tlg001",
            passage="1.1@μῆνιν-1.1@θεά"
        )
        assert urn.passage == "1.1@μῆνιν-1.1@θεά"
        assert urn.has_subreference() is True

    def test_valid_subreference_from_string_single_passage(self):
        """Test that from_string accepts single @ in passage."""
        urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@μῆνιν")
        assert urn.passage == "1.1@μῆνιν"
        assert urn.has_subreference() is True

    def test_valid_subreference_from_string_range(self):
        """Test that from_string accepts single @ in range parts."""
        urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@μῆνιν-1.1@θεά")
        assert urn.passage == "1.1@μῆνιν-1.1@θεά"
        assert urn.has_subreference() is True

    def test_empty_subreference_single_passage_constructor(self):
        """Test that empty subreference in single passage raises ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1@"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_single_passage_from_string(self):
        """Test that empty subreference in single passage raises ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@")
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_first_part_constructor(self):
        """Test that empty subreference in first range part raises ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1@-1.2"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_first_part_from_string(self):
        """Test that empty subreference in first range part raises ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@-1.2")
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_second_part_constructor(self):
        """Test that empty subreference in second range part raises ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1-1.2@"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_second_part_from_string(self):
        """Test that empty subreference in second range part raises ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1-1.2@")
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_both_range_parts_constructor(self):
        """Test that empty subreferences in both range parts raise ValueError in constructor."""
        with pytest.raises(ValidationError) as exc_info:
            CtsUrn(
                urn_type="cts",
                namespace="greekLit",
                text_group="tlg0012",
                work="tlg001",
                passage="1.1@-1.2@"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_both_range_parts_from_string(self):
        """Test that empty subreferences in both range parts raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.tlg001:1.1@-1.2@")
        assert "Subreference cannot be empty" in str(exc_info.value)


class TestCtsUrnValidString:
    """Tests for the valid_string classmethod."""

    def test_valid_string_basic(self):
        """Test valid_string returns True for a valid basic URN."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:") is True

    def test_valid_string_with_passage(self):
        """Test valid_string returns True for a valid URN with passage."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1.1") is True

    def test_valid_string_with_range(self):
        """Test valid_string returns True for a valid URN with range."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1.1-1.5") is True

    def test_valid_string_with_work_hierarchy(self):
        """Test valid_string returns True for a valid URN with work hierarchy."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012.001.wacl1.ex1:1.1") is True

    def test_valid_string_too_few_components(self):
        """Test valid_string returns False for too few components."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012") is False

    def test_valid_string_too_many_components(self):
        """Test valid_string returns False for too many components."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1.1:extra") is False

    def test_valid_string_too_many_hyphens(self):
        """Test valid_string returns False for too many hyphens in passage."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1.1-1.5-2.1") is False

    def test_valid_string_too_many_dots(self):
        """Test valid_string returns False for too many dots in work component."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012.001.wacl1.ex1.extra:1.1") is False

    def test_valid_string_invalid_input(self):
        """Test valid_string returns False for invalid input."""
        assert CtsUrn.valid_string("") is False
        assert CtsUrn.valid_string("not:a:urn") is False

    def test_valid_string_successive_periods_in_work(self):
        """Test valid_string returns False for successive periods in work component."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012..001:") is False
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012.001..wacl1:") is False
        assert CtsUrn.valid_string("urn:cts:greekLit:..tlg0012:") is False

    def test_valid_string_successive_periods_in_passage(self):
        """Test valid_string returns False for successive periods in passage component."""
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1..1") is False
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1.1-1..5") is False
        assert CtsUrn.valid_string("urn:cts:greekLit:tlg0012:..1.1") is False


class TestCtsUrnFromString:
    """Tests for the from_string classmethod."""

    def test_from_string_successive_periods_in_work(self):
        """Test from_string raises ValueError for successive periods in work component."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012..001:")
        assert "successive periods" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012.001..wacl1:")
        assert "successive periods" in str(exc_info.value)

    def test_from_string_successive_periods_in_passage(self):
        """Test from_string raises ValueError for successive periods in passage component."""
        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012:1..1")
        assert "successive periods" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            CtsUrn.from_string("urn:cts:greekLit:tlg0012:1.1-1..5")
        assert "successive periods" in str(exc_info.value)


class TestCtsUrnWorkEquals:
    """Tests for the work_equals method."""

    def test_work_equals_identical_urns(self):
        """Test work_equals returns True for identical work hierarchies."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        assert urn1.work_equals(urn2) is True

    def test_work_equals_different_text_group(self):
        """Test work_equals returns False for different text_group."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0013"
        )
        assert urn1.work_equals(urn2) is False

    def test_work_equals_different_work(self):
        """Test work_equals returns False for different work."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="002"
        )
        assert urn1.work_equals(urn2) is False

    def test_work_equals_ignores_passage(self):
        """Test work_equals ignores passage component."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.2"
        )
        assert urn1.work_equals(urn2) is True


class TestCtsUrnWorkContains:
    """Tests for the work_contains method."""

    def test_work_contains_identical_urns(self):
        """Test work_contains returns True for identical work hierarchies."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        assert urn1.work_contains(urn2) is True

    def test_work_contains_with_none_fields(self):
        """Test work_contains returns True when non-None fields match."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        assert urn1.work_contains(urn2) is True

    def test_work_contains_mismatch_non_none_field(self):
        """Test work_contains returns False when non-None fields don't match."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="002"
        )
        assert urn1.work_contains(urn2) is False

    def test_work_contains_all_none_fields(self):
        """Test work_contains returns True when all fields are None."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        assert urn1.work_contains(urn2) is True


class TestCtsUrnPassageEquals:
    """Tests for the passage_equals method."""

    def test_passage_equals_same_passage(self):
        """Test passage_equals returns True for identical passages."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn1.passage_equals(urn2) is True

    def test_passage_equals_different_passage(self):
        """Test passage_equals returns False for different passages."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.2"
        )
        assert urn1.passage_equals(urn2) is False

    def test_passage_equals_both_none(self):
        """Test passage_equals returns True when both passages are None."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn1.passage_equals(urn2) is True


class TestCtsUrnPassageContains:
    """Tests for the passage_contains method."""

    def test_passage_contains_identical(self):
        """Test passage_contains returns True for identical passages."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        assert urn1.passage_contains(urn2) is True

    def test_passage_contains_refinement(self):
        """Test passage_contains returns True for refinement passages."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.11"
        )
        assert urn1.passage_contains(urn2) is True

    def test_passage_contains_no_refinement_single_char(self):
        """Test passage_contains returns False for single char without dot."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="12"
        )
        assert urn1.passage_contains(urn2) is False

    def test_passage_contains_completely_different(self):
        """Test passage_contains returns False for different passages."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="2.2"
        )
        assert urn1.passage_contains(urn2) is False

    def test_passage_contains_both_none(self):
        """Test passage_contains returns True when both passages are None."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        assert urn1.passage_contains(urn2) is True

    def test_passage_contains_raises_on_self_range(self):
        """Test passage_contains raises ValueError when self is a range."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        with pytest.raises(ValueError) as exc_info:
            urn1.passage_contains(urn2)
        assert "range passage" in str(exc_info.value)

    def test_passage_contains_raises_on_other_range(self):
        """Test passage_contains raises ValueError when other is a range."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        with pytest.raises(ValueError) as exc_info:
            urn1.passage_contains(urn2)
        assert "range passage" in str(exc_info.value)


class TestCtsUrnContains:
    """Tests for the contains method."""

    def test_contains_identical_urns(self):
        """Test contains returns True for identical URNs."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        assert urn1.contains(urn2) is True

    def test_contains_similar_work_and_passage(self):
        """Test contains returns True for similar work and passage."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.11"
        )
        assert urn1.contains(urn2) is True

    def test_contains_different_work(self):
        """Test contains returns False if work is different."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="002",
            passage="1.1"
        )
        assert urn1.contains(urn2) is False

    def test_contains_different_passage(self):
        """Test contains returns False if passage is different."""
        urn1 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        urn2 = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="2.1"
        )
        assert urn1.contains(urn2) is False


class TestCtsUrnRoundTrip:
    """Tests for round-trip conversion (from_string -> str)."""

    def test_roundtrip_basic_urn(self):
        """Test round-trip for a basic URN."""
        urn_string = "urn:cts:greekLit:tlg0012:"
        urn = CtsUrn.from_string(urn_string)
        assert str(urn) == urn_string

    def test_roundtrip_with_work_hierarchy(self):
        """Test round-trip conversion with work hierarchy."""
        urn_string = "urn:cts:greekLit:tlg0012.001.wacl1.ex1:"
        urn = CtsUrn.from_string(urn_string)
        assert str(urn) == urn_string

    def test_roundtrip_with_passage(self):
        """Test round-trip conversion with passage."""
        urn_string = "urn:cts:greekLit:tlg0012:1.1-1.5"
        urn = CtsUrn.from_string(urn_string)
        assert str(urn) == urn_string

    def test_roundtrip_with_all_components(self):
        """Test round-trip conversion with all components."""
        urn_string = "urn:cts:greekLit:tlg0012.001.wacl1:1.1"
        urn = CtsUrn.from_string(urn_string)
        assert str(urn) == urn_string


class TestCtsUrnDropPassage:
    """Tests for the drop_passage method."""

    def test_drop_passage_with_simple_passage(self):
        """Test drop_passage removes a simple passage component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        result = urn.drop_passage()
        assert result.passage is None
        assert result.text_group == "tlg0012"
        assert result.work == "001"

    def test_drop_passage_with_range(self):
        """Test drop_passage removes a range passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        result = urn.drop_passage()
        assert result.passage is None
        assert result.text_group == "tlg0012"

    def test_drop_passage_with_none_passage(self):
        """Test drop_passage when passage is already None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        result = urn.drop_passage()
        assert result.passage is None
        assert result.text_group == "tlg0012"

    def test_drop_passage_preserves_all_work_hierarchy(self):
        """Test drop_passage preserves all work hierarchy components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.drop_passage()
        assert result.passage is None
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.version == "wacl1"
        assert result.exemplar == "ex1"

    def test_drop_passage_creates_new_instance(self):
        """Test drop_passage returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        result = urn.drop_passage()
        assert result is not urn
        assert urn.passage == "1.1"  # Original unchanged

    def test_drop_passage_serialization(self):
        """Test that drop_passage result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1-2.1"
        )
        result = urn.drop_passage()
        assert str(result) == "urn:cts:greekLit:tlg0012.001:"


class TestCtsUrnDropSubreference:
    """Tests for the drop_subreference method."""

    def test_drop_subreference_single_passage_with_subreference(self):
        """Test drop_subreference removes subreference from single passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1@μῆνιν"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1"
        assert result.text_group == "tlg0012"
        assert result.work == "001"

    def test_drop_subreference_single_passage_without_subreference(self):
        """Test drop_subreference returns same passage when no subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1"
        assert result.text_group == "tlg0012"

    def test_drop_subreference_range_with_subreference_on_both_parts(self):
        """Test drop_subreference removes subreferences from both range parts."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1@μῆνιν-1.2@θεά"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1-1.2"
        assert result.text_group == "tlg0012"

    def test_drop_subreference_range_with_subreference_on_first_part(self):
        """Test drop_subreference removes subreference from first range part only."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1@μῆνιν-1.2"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1-1.2"

    def test_drop_subreference_range_with_subreference_on_second_part(self):
        """Test drop_subreference removes subreference from second range part only."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1-1.2@θεά"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1-1.2"

    def test_drop_subreference_range_without_subreference(self):
        """Test drop_subreference returns same passage for range without subreference."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1-1.5"

    def test_drop_subreference_with_none_passage(self):
        """Test drop_subreference when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        result = urn.drop_subreference()
        assert result.passage is None

    def test_drop_subreference_preserves_all_work_hierarchy(self):
        """Test drop_subreference preserves all work hierarchy components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1@word"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1"
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.version == "wacl1"
        assert result.exemplar == "ex1"

    def test_drop_subreference_creates_new_instance(self):
        """Test drop_subreference returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1@word"
        )
        result = urn.drop_subreference()
        assert result is not urn
        assert urn.passage == "1.1@word"  # Original unchanged

    def test_drop_subreference_serialization(self):
        """Test that drop_subreference result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1@word1-2.1@word2"
        )
        result = urn.drop_subreference()
        assert str(result) == "urn:cts:greekLit:tlg0012.001:1.1-2.1"

    def test_drop_subreference_with_complex_subreference(self):
        """Test drop_subreference with complex subreference strings."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1@word[1,2,3]-1.2@word[4,5,6]"
        )
        result = urn.drop_subreference()
        assert result.passage == "1.1-1.2"


class TestCtsUrnSetPassage:
    """Tests for the set_passage method."""

    def test_set_passage_from_none(self):
        """Test set_passage adds a passage when passage is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        result = urn.set_passage("1.1")
        assert result.passage == "1.1"
        assert result.text_group == "tlg0012"

    def test_set_passage_replaces_existing(self):
        """Test set_passage replaces an existing passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        result = urn.set_passage("2.5")
        assert result.passage == "2.5"
        assert result.text_group == "tlg0012"

    def test_set_passage_with_range(self):
        """Test set_passage with a range passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        result = urn.set_passage("1.1-1.10")
        assert result.passage == "1.1-1.10"
        assert result.is_range() is True

    def test_set_passage_replaces_range_with_single(self):
        """Test set_passage replaces a range with a single passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1-1.5"
        )
        result = urn.set_passage("2.3")
        assert result.passage == "2.3"
        assert result.is_range() is False

    def test_set_passage_preserves_all_work_hierarchy(self):
        """Test set_passage preserves all work hierarchy components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.set_passage("2.5")
        assert result.passage == "2.5"
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.version == "wacl1"
        assert result.exemplar == "ex1"

    def test_set_passage_creates_new_instance(self):
        """Test set_passage returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            passage="1.1"
        )
        result = urn.set_passage("2.5")
        assert result is not urn
        assert urn.passage == "1.1"  # Original unchanged

    def test_set_passage_serialization(self):
        """Test that set_passage result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        result = urn.set_passage("3.14")
        assert str(result) == "urn:cts:greekLit:tlg0012.001:3.14"

    def test_set_passage_with_complex_hierarchical_passage(self):
        """Test set_passage with a complex hierarchical passage."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        result = urn.set_passage("1.2.3.4")
        assert result.passage == "1.2.3.4"
        assert str(result) == "urn:cts:greekLit:tlg0012.001:1.2.3.4"

    def test_set_passage_empty_string(self):
        """Test set_passage with an empty string."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        result = urn.set_passage("")
        assert result.passage == ""
        assert str(result) == "urn:cts:greekLit:tlg0012:"


class TestCtsUrnDropVersion:
    """Tests for the drop_version method."""

    def test_drop_version_with_version_present(self):
        """Test drop_version removes a version component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.drop_version()
        assert result.version is None
        assert result.text_group == "tlg0012"
        assert result.work == "001"

    def test_drop_version_when_none(self):
        """Test drop_version when version is already None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        result = urn.drop_version()
        assert result.version is None
        assert result.work == "001"

    def test_drop_version_also_drops_exemplar(self):
        """Test drop_version also removes exemplar component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        result = urn.drop_version()
        assert result.version is None
        assert result.exemplar is None  # Exemplar must be dropped too

    def test_drop_version_preserves_passage(self):
        """Test drop_version preserves passage component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            passage="1.1"
        )
        result = urn.drop_version()
        assert result.version is None
        assert result.passage == "1.1"

    def test_drop_version_preserves_all_other_components(self):
        """Test drop_version preserves all non-version/exemplar components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.drop_version()
        assert result.version is None
        assert result.exemplar is None  # Also dropped with version
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.passage == "1.1"

    def test_drop_version_creates_new_instance(self):
        """Test drop_version returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.drop_version()
        assert result is not urn
        assert urn.version == "wacl1"  # Original unchanged

    def test_drop_version_serialization(self):
        """Test that drop_version result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            passage="1.1"
        )
        result = urn.drop_version()
        assert str(result) == "urn:cts:greekLit:tlg0012.001:1.1"


class TestCtsUrnSetVersion:
    """Tests for the set_version method."""

    def test_set_version_from_none(self):
        """Test set_version adds a version when version is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        result = urn.set_version("wacl1")
        assert result.version == "wacl1"
        assert result.work == "001"

    def test_set_version_replaces_existing(self):
        """Test set_version replaces an existing version."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.set_version("perseus1")
        assert result.version == "perseus1"
        assert result.work == "001"

    def test_set_version_preserves_exemplar(self):
        """Test set_version preserves exemplar component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="old",
            exemplar="ex1"
        )
        result = urn.set_version("wacl1")
        assert result.version == "wacl1"
        assert result.exemplar == "ex1"

    def test_set_version_preserves_passage(self):
        """Test set_version preserves passage component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        result = urn.set_version("wacl1")
        assert result.version == "wacl1"
        assert result.passage == "1.1"

    def test_set_version_preserves_all_other_components(self):
        """Test set_version preserves all non-version components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="old",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.set_version("new")
        assert result.version == "new"
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.exemplar == "ex1"
        assert result.passage == "1.1"

    def test_set_version_creates_new_instance(self):
        """Test set_version returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.set_version("perseus1")
        assert result is not urn
        assert urn.version == "wacl1"  # Original unchanged

    def test_set_version_serialization(self):
        """Test that set_version result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            passage="1.1"
        )
        result = urn.set_version("wacl1")
        assert str(result) == "urn:cts:greekLit:tlg0012.001.wacl1:1.1"

    def test_set_version_empty_string(self):
        """Test set_version with an empty string."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        result = urn.set_version("")
        assert result.version == ""

    def test_set_version_fails_without_work(self):
        """Test set_version raises error when work is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        with pytest.raises(ValidationError) as exc_info:
            urn.set_version("wacl1")
        assert "version cannot be set when work is None" in str(exc_info.value)


class TestCtsUrnDropExemplar:
    """Tests for the drop_exemplar method."""

    def test_drop_exemplar_with_exemplar_present(self):
        """Test drop_exemplar removes an exemplar component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        result = urn.drop_exemplar()
        assert result.exemplar is None
        assert result.version == "wacl1"

    def test_drop_exemplar_when_none(self):
        """Test drop_exemplar when exemplar is already None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.drop_exemplar()
        assert result.exemplar is None
        assert result.version == "wacl1"

    def test_drop_exemplar_preserves_version(self):
        """Test drop_exemplar preserves version component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        result = urn.drop_exemplar()
        assert result.exemplar is None
        assert result.version == "wacl1"

    def test_drop_exemplar_preserves_passage(self):
        """Test drop_exemplar preserves passage component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.drop_exemplar()
        assert result.exemplar is None
        assert result.passage == "1.1"

    def test_drop_exemplar_preserves_all_other_components(self):
        """Test drop_exemplar preserves all non-exemplar components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.drop_exemplar()
        assert result.exemplar is None
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.version == "wacl1"
        assert result.passage == "1.1"

    def test_drop_exemplar_creates_new_instance(self):
        """Test drop_exemplar returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        result = urn.drop_exemplar()
        assert result is not urn
        assert urn.exemplar == "ex1"  # Original unchanged

    def test_drop_exemplar_serialization(self):
        """Test that drop_exemplar result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1",
            passage="1.1"
        )
        result = urn.drop_exemplar()
        assert str(result) == "urn:cts:greekLit:tlg0012.001.wacl1:1.1"


class TestCtsUrnSetExemplar:
    """Tests for the set_exemplar method."""

    def test_set_exemplar_from_none(self):
        """Test set_exemplar adds an exemplar when exemplar is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.set_exemplar("ex1")
        assert result.exemplar == "ex1"
        assert result.version == "wacl1"

    def test_set_exemplar_replaces_existing(self):
        """Test set_exemplar replaces an existing exemplar."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        result = urn.set_exemplar("ex2")
        assert result.exemplar == "ex2"
        assert result.version == "wacl1"

    def test_set_exemplar_preserves_version(self):
        """Test set_exemplar preserves version component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.set_exemplar("ex1")
        assert result.exemplar == "ex1"
        assert result.version == "wacl1"

    def test_set_exemplar_preserves_passage(self):
        """Test set_exemplar preserves passage component."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            passage="1.1"
        )
        result = urn.set_exemplar("ex1")
        assert result.exemplar == "ex1"
        assert result.passage == "1.1"

    def test_set_exemplar_preserves_all_other_components(self):
        """Test set_exemplar preserves all non-exemplar components."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="old",
            passage="1.1"
        )
        result = urn.set_exemplar("new")
        assert result.exemplar == "new"
        assert result.urn_type == "cts"
        assert result.namespace == "greekLit"
        assert result.text_group == "tlg0012"
        assert result.work == "001"
        assert result.version == "wacl1"
        assert result.passage == "1.1"

    def test_set_exemplar_creates_new_instance(self):
        """Test set_exemplar returns a new CtsUrn instance."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            exemplar="ex1"
        )
        result = urn.set_exemplar("ex2")
        assert result is not urn
        assert urn.exemplar == "ex1"  # Original unchanged

    def test_set_exemplar_serialization(self):
        """Test that set_exemplar result can be serialized correctly."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1",
            passage="1.1"
        )
        result = urn.set_exemplar("ex1")
        assert str(result) == "urn:cts:greekLit:tlg0012.001.wacl1.ex1:1.1"

    def test_set_exemplar_empty_string(self):
        """Test set_exemplar with an empty string."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001",
            version="wacl1"
        )
        result = urn.set_exemplar("")
        assert result.exemplar == ""

    def test_set_exemplar_fails_without_work(self):
        """Test set_exemplar raises error when work is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012"
        )
        with pytest.raises(ValidationError) as exc_info:
            urn.set_exemplar("ex1")
        assert "exemplar cannot be set when work is None" in str(exc_info.value)

    def test_set_exemplar_fails_without_version(self):
        """Test set_exemplar raises error when version is None."""
        urn = CtsUrn(
            urn_type="cts",
            namespace="greekLit",
            text_group="tlg0012",
            work="001"
        )
        with pytest.raises(ValidationError) as exc_info:
            urn.set_exemplar("ex1")
        assert "exemplar cannot be set when version is None" in str(exc_info.value)
