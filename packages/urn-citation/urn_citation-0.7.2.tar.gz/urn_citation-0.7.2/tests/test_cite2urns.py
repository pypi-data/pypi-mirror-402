import pytest

from urn_citation import Cite2Urn


class TestCite2UrnFromString:
    def test_parses_full_with_version(self):
        urn = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:codexmodel")
        assert urn.urn_type == "cite2"
        assert urn.namespace == "hmt"
        assert urn.collection == "datamodels"
        assert urn.version == "v1"
        assert urn.object_id == "codexmodel"

    def test_parses_without_version_and_with_range_object(self):
        urn = Cite2Urn.from_string("urn:cite2:ns:coll:obj-2")
        assert urn.urn_type == "cite2"
        assert urn.namespace == "ns"
        assert urn.collection == "coll"
        assert urn.version is None
        assert urn.object_id == "obj-2"

    def test_requires_cite2_prefix(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cts:ns:coll:obj")
        assert "start with 'urn:cite2:'" in str(exc_info.value)

    def test_requires_five_colon_parts(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:coll")
        assert "5 colon-delimited parts" in str(exc_info.value)

    def test_collection_cannot_end_with_period(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:coll.:obj")
        assert "end with a period" in str(exc_info.value)

    def test_collection_allows_single_period_only(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:coll.v1.extra:obj")
        assert "at most one period" in str(exc_info.value)

    def test_collection_parts_must_be_non_empty(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:.v1:obj")
        assert "non-empty" in str(exc_info.value)

    def test_object_cannot_end_with_hyphen(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:coll:obj-")
        assert "end with a hyphen" in str(exc_info.value)

    def test_object_allows_single_hyphen_only(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:coll:one-two-three")
        assert "at most one hyphen" in str(exc_info.value)

    def test_object_parts_must_be_non_empty(self):
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:ns:coll:-obj")
        assert "non-empty identifiers" in str(exc_info.value)

    def test_namespace_and_collection_and_object_required(self):
        for urn in [
            "urn:cite2::coll:obj",  # missing namespace
            "urn:cite2:ns::obj",    # missing collection
            "urn:cite2:ns:coll:",   # missing object
        ]:
            with pytest.raises(ValueError):
                Cite2Urn.from_string(urn)


class TestCite2UrnToString:
    def test_to_string_with_version(self):
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="datamodels",
            version="v1",
            object_id="codexmodel",
        )

        assert str(urn) == "urn:cite2:hmt:datamodels.v1:codexmodel"

    def test_to_string_without_version(self):
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="ns",
            collection="coll",
            object_id="obj-2",
        )

        assert str(urn) == "urn:cite2:ns:coll:obj-2"

    def test_roundtrip_from_string_and_back(self):
        raw = "urn:cite2:hmt:datamodels.v1:codexmodel"
        urn = Cite2Urn.from_string(raw)
        assert str(urn) == raw

    def test_roundtrip_without_version(self):
        raw = "urn:cite2:ns:coll:obj"
        urn = Cite2Urn.from_string(raw)
        assert str(urn) == raw


class TestCite2UrnRangeHelpers:
    def test_is_range_true(self):
        urn = Cite2Urn.from_string("urn:cite2:ns:coll:obj-2")
        assert urn.is_range() is True

    def test_is_range_false_single_object(self):
        urn = Cite2Urn.from_string("urn:cite2:ns:coll:obj")
        assert urn.is_range() is False

    def test_range_begin_and_end(self):
        urn = Cite2Urn.from_string("urn:cite2:ns:coll:obj-2")
        assert urn.range_begin() == "obj"
        assert urn.range_end() == "2"

    def test_range_helpers_none_when_not_range(self):
        urn = Cite2Urn.from_string("urn:cite2:ns:coll:obj")
        assert urn.range_begin() is None
        assert urn.range_end() is None


class TestCite2UrnValidString:
    def test_valid_basic_and_with_version_and_range(self):
        assert Cite2Urn.valid_string("urn:cite2:ns:coll:obj") is True
        assert Cite2Urn.valid_string("urn:cite2:ns:coll.v1:obj") is True
        assert Cite2Urn.valid_string("urn:cite2:ns:coll:obj-2") is True

    def test_invalid_prefix_or_parts(self):
        assert Cite2Urn.valid_string("urn:cts:ns:coll:obj") is False
        assert Cite2Urn.valid_string("urn:cite2:ns:coll") is False

    def test_invalid_collection_rules(self):
        assert Cite2Urn.valid_string("urn:cite2:ns:coll.:obj") is False
        assert Cite2Urn.valid_string("urn:cite2:ns:coll.v1.extra:obj") is False
        assert Cite2Urn.valid_string("urn:cite2:ns:.v1:obj") is False

    def test_invalid_object_rules(self):
        assert Cite2Urn.valid_string("urn:cite2:ns:coll:obj-") is False
        assert Cite2Urn.valid_string("urn:cite2:ns:coll:one-two-three") is False
        assert Cite2Urn.valid_string("urn:cite2:ns:coll:-obj") is False

    def test_missing_namespace_collection_or_object(self):
        assert Cite2Urn.valid_string("urn:cite2::coll:obj") is False
        assert Cite2Urn.valid_string("urn:cite2:ns::obj") is False
        assert Cite2Urn.valid_string("urn:cite2:ns:coll:") is False


class TestCite2UrnCollectionEquals:
    def test_identical_collections(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj2"
        )
        assert urn1.collection_equals(urn2) is True

    def test_different_namespace(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="other",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        assert urn1.collection_equals(urn2) is False

    def test_different_collection(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="other",
            object_id="obj1"
        )
        assert urn1.collection_equals(urn2) is False

    def test_different_version(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v2",
            object_id="obj1"
        )
        assert urn1.collection_equals(urn2) is False


class TestCite2UrnCollectionContains:
    def test_identical_contains(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj2"
        )
        assert urn1.collection_contains(urn2) is True

    def test_partial_constraints_contains(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj2"
        )
        assert urn1.collection_contains(urn2) is True

    def test_namespace_mismatch_not_contained(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="other",
            collection="data",
            object_id="obj1"
        )
        assert urn1.collection_contains(urn2) is False

    def test_version_constraint_mismatch(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v2",
            object_id="obj1"
        )
        assert urn1.collection_contains(urn2) is False


class TestCite2UrnObjectEquals:
    def test_identical_objects(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="other",
            collection="other",
            object_id="obj1"
        )
        assert urn1.object_equals(urn2) is True

    def test_different_objects(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj2"
        )
        assert urn1.object_equals(urn2) is False

    def test_range_object_equality(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        assert urn1.object_equals(urn2) is True


class TestCite2UrnDropMethods:
    def test_drop_version(self):
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        dropped = urn.drop_version()
        assert dropped.urn_type == "cite2"
        assert dropped.namespace == "hmt"
        assert dropped.collection == "data"
        assert dropped.version is None
        assert dropped.object_id == "obj1"

    def test_drop_version_already_none(self):
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        dropped = urn.drop_version()
        assert dropped.version is None
        assert dropped.object_id == "obj1"

    def test_drop_objectid(self):
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        dropped = urn.drop_objectid()
        assert dropped.urn_type == "cite2"
        assert dropped.namespace == "hmt"
        assert dropped.collection == "data"
        assert dropped.version == "v1"
        assert dropped.object_id is None

    def test_drop_objectid_already_none(self):
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        dropped = urn.drop_objectid()
        assert dropped.object_id is None
        assert dropped.collection == "data"

    def test_drop_subreference_single_object_with_subreference(self):
        """Test drop_subreference removes subreference from single object."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1"
        assert result.namespace == "hmt"
        assert result.collection == "data"

    def test_drop_subreference_single_object_without_subreference(self):
        """Test drop_subreference returns same object_id when no subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1"

    def test_drop_subreference_range_with_subreference_on_both_parts(self):
        """Test drop_subreference removes subreferences from both range parts."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1-obj2"

    def test_drop_subreference_range_with_subreference_on_first_part(self):
        """Test drop_subreference removes subreference from first range part only."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1-obj2"

    def test_drop_subreference_range_with_subreference_on_second_part(self):
        """Test drop_subreference removes subreference from second range part only."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1-obj2"

    def test_drop_subreference_range_without_subreference(self):
        """Test drop_subreference returns same object_id for range without subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1-obj2"

    def test_drop_subreference_with_none_object_id(self):
        """Test drop_subreference when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        result = urn.drop_subreference()
        assert result.object_id is None

    def test_drop_subreference_preserves_all_collection_hierarchy(self):
        """Test drop_subreference preserves all collection hierarchy components."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1@region"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1"
        assert result.urn_type == "cite2"
        assert result.namespace == "hmt"
        assert result.collection == "data"
        assert result.version == "v1"

    def test_drop_subreference_creates_new_instance(self):
        """Test drop_subreference returns a new Cite2Urn instance."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region"
        )
        result = urn.drop_subreference()
        assert result is not urn
        assert urn.object_id == "obj1@region"  # Original unchanged

    def test_drop_subreference_serialization(self):
        """Test that drop_subreference result can be serialized correctly."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1@region1-obj2@region2"
        )
        result = urn.drop_subreference()
        assert str(result) == "urn:cite2:hmt:data.v1:obj1-obj2"

    def test_drop_subreference_with_complex_subreference(self):
        """Test drop_subreference with complex subreference strings."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@roi[1,2,3,4]-obj2@roi[5,6,7,8]"
        )
        result = urn.drop_subreference()
        assert result.object_id == "obj1-obj2"

class TestCite2UrnContains:
    def test_contains_identical_urns(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        assert urn1.contains(urn2) is True

    def test_contains_partial_collection_and_equal_object(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            version="v1",
            object_id="obj1"
        )
        assert urn1.contains(urn2) is True

    def test_contains_false_different_objects(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj2"
        )
        assert urn1.contains(urn2) is False

    def test_contains_false_different_collection(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data1",
            object_id="obj1"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data2",
            object_id="obj1"
        )
        assert urn1.contains(urn2) is False

    def test_contains_requires_exact_object_match(self):
        urn1 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj"
        )
        urn2 = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj-sub"
        )
        # Even though collection_contains would be True,
        # contains is False because objects are not equal
        assert urn1.contains(urn2) is False


class TestCite2UrnHasSubreference:
    """Tests for the has_subreference method."""

    def test_has_subreference_single_object_with_subreference(self):
        """Test has_subreference returns True for a single object with subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_single_object_without_subreference(self):
        """Test has_subreference returns False for a single object without subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        assert urn.has_subreference() is False

    def test_has_subreference_range_with_subreference_on_both_parts(self):
        """Test has_subreference returns True when both range parts have subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_range_with_subreference_on_first_part(self):
        """Test has_subreference returns True when only first range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_range_with_subreference_on_second_part(self):
        """Test has_subreference returns True when only second range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        assert urn.has_subreference() is True

    def test_has_subreference_range_without_subreference(self):
        """Test has_subreference returns False for a range without any subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        assert urn.has_subreference() is False

    def test_has_subreference_none_object(self):
        """Test has_subreference returns False when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        assert urn.has_subreference() is False


class TestCite2UrnHasSubreference1:
    """Tests for the has_subreference1 method."""

    def test_has_subreference1_range_with_subreference_on_first_part(self):
        """Test has_subreference1 returns True when first range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        assert urn.has_subreference1() is True

    def test_has_subreference1_range_without_subreference_on_first_part(self):
        """Test has_subreference1 returns False when first range part lacks subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        assert urn.has_subreference1() is False

    def test_has_subreference1_range_with_subreference_on_both_parts(self):
        """Test has_subreference1 returns True when both range parts have subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        assert urn.has_subreference1() is True

    def test_has_subreference1_range_without_any_subreference(self):
        """Test has_subreference1 returns False when neither range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        assert urn.has_subreference1() is False

    def test_has_subreference1_raises_error_on_single_object(self):
        """Test has_subreference1 raises ValueError when URN is not a range."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference1()
        assert "has_subreference1 can only be called on range URNs" in str(exc_info.value)

    def test_has_subreference1_raises_error_on_none_object(self):
        """Test has_subreference1 raises ValueError when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference1()
        assert "has_subreference1 can only be called on range URNs" in str(exc_info.value)


class TestCite2UrnHasSubreference2:
    """Tests for the has_subreference2 method."""

    def test_has_subreference2_range_with_subreference_on_second_part(self):
        """Test has_subreference2 returns True when second range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        assert urn.has_subreference2() is True

    def test_has_subreference2_range_without_subreference_on_second_part(self):
        """Test has_subreference2 returns False when second range part lacks subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        assert urn.has_subreference2() is False

    def test_has_subreference2_range_with_subreference_on_both_parts(self):
        """Test has_subreference2 returns True when both range parts have subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        assert urn.has_subreference2() is True

    def test_has_subreference2_range_without_any_subreference(self):
        """Test has_subreference2 returns False when neither range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        assert urn.has_subreference2() is False

    def test_has_subreference2_raises_error_on_single_object(self):
        """Test has_subreference2 raises ValueError when URN is not a range."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj2@region2"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference2()
        assert "has_subreference2 can only be called on range URNs" in str(exc_info.value)

    def test_has_subreference2_raises_error_on_none_object(self):
        """Test has_subreference2 raises ValueError when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.has_subreference2()
        assert "has_subreference2 can only be called on range URNs" in str(exc_info.value)


class TestCite2UrnSubreference:
    """Tests for the subreference method."""

    def test_subreference_single_object_with_subreference(self):
        """Test subreference returns the subreference part for a single object."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1"
        )
        assert urn.subreference() == "region1"

    def test_subreference_single_object_without_subreference(self):
        """Test subreference returns None for a single object without subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1"
        )
        assert urn.subreference() is None

    def test_subreference_none_object(self):
        """Test subreference returns None when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        assert urn.subreference() is None

    def test_subreference_raises_error_on_range(self):
        """Test subreference raises ValueError when URN is a range."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference()
        assert "subreference can only be called on non-range URNs" in str(exc_info.value)

    def test_subreference_raises_error_on_range_without_subreference(self):
        """Test subreference raises ValueError for a range without subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference()
        assert "subreference can only be called on non-range URNs" in str(exc_info.value)

    def test_subreference_with_complex_subreference(self):
        """Test subreference with a complex subreference string."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@roi[1,2,3,4]"
        )
        assert urn.subreference() == "roi[1,2,3,4]"


class TestCite2UrnSubreference1:
    """Tests for the subreference1 method."""

    def test_subreference1_range_with_subreference_on_first_part(self):
        """Test subreference1 returns the subreference part of the range begin."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        assert urn.subreference1() == "region1"

    def test_subreference1_range_without_subreference_on_first_part(self):
        """Test subreference1 returns None when first range part lacks subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        assert urn.subreference1() is None

    def test_subreference1_range_with_subreference_on_both_parts(self):
        """Test subreference1 returns the first subreference when both parts have subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        assert urn.subreference1() == "region1"

    def test_subreference1_range_without_any_subreference(self):
        """Test subreference1 returns None when neither range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        assert urn.subreference1() is None

    def test_subreference1_raises_error_on_single_object(self):
        """Test subreference1 raises ValueError when URN is not a range."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference1()
        assert "subreference1 can only be called on range URNs" in str(exc_info.value)

    def test_subreference1_raises_error_on_none_object(self):
        """Test subreference1 raises ValueError when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference1()
        assert "subreference1 can only be called on range URNs" in str(exc_info.value)

    def test_subreference1_with_complex_subreference(self):
        """Test subreference1 with a complex subreference string."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@roi[1,2,3,4]-obj2"
        )
        assert urn.subreference1() == "roi[1,2,3,4]"


class TestCite2UrnSubreference2:
    """Tests for the subreference2 method."""

    def test_subreference2_range_with_subreference_on_second_part(self):
        """Test subreference2 returns the subreference part of the range end."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        assert urn.subreference2() == "region2"

    def test_subreference2_range_without_subreference_on_second_part(self):
        """Test subreference2 returns None when second range part lacks subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        assert urn.subreference2() is None

    def test_subreference2_range_with_subreference_on_both_parts(self):
        """Test subreference2 returns the second subreference when both parts have subreferences."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        assert urn.subreference2() == "region2"

    def test_subreference2_range_without_any_subreference(self):
        """Test subreference2 returns None when neither range part has subreference."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2"
        )
        assert urn.subreference2() is None

    def test_subreference2_raises_error_on_single_object(self):
        """Test subreference2 raises ValueError when URN is not a range."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj2@region2"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference2()
        assert "subreference2 can only be called on range URNs" in str(exc_info.value)

    def test_subreference2_raises_error_on_none_object(self):
        """Test subreference2 raises ValueError when object_id is None."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data"
        )
        with pytest.raises(ValueError) as exc_info:
            urn.subreference2()
        assert "subreference2 can only be called on range URNs" in str(exc_info.value)

    def test_subreference2_with_complex_subreference(self):
        """Test subreference2 with a complex subreference string."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@roi[5,6,7,8]"
        )
        assert urn.subreference2() == "roi[5,6,7,8]"


class TestCite2UrnSubreferenceValidation:
    """Tests for subreference validation in Cite2Urn."""

    def test_multiple_subreferences_in_single_object_constructor(self):
        """Test that multiple @ signs in a single object raise ValueError in constructor."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Cite2Urn(
                urn_type="cite2",
                namespace="hmt",
                collection="data",
                object_id="obj1@region1@region2"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_single_object_from_string(self):
        """Test that multiple @ signs in a single object raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:hmt:data:obj1@region1@region2")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_first_part_constructor(self):
        """Test that multiple @ signs in first range part raise ValueError in constructor."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Cite2Urn(
                urn_type="cite2",
                namespace="hmt",
                collection="data",
                object_id="obj1@region1@extra-obj2"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_first_part_from_string(self):
        """Test that multiple @ signs in first range part raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:hmt:data:obj1@region1@extra-obj2")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_second_part_constructor(self):
        """Test that multiple @ signs in second range part raise ValueError in constructor."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Cite2Urn(
                urn_type="cite2",
                namespace="hmt",
                collection="data",
                object_id="obj1-obj2@region2@extra"
            )
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_multiple_subreferences_in_range_second_part_from_string(self):
        """Test that multiple @ signs in second range part raise ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:hmt:data:obj1-obj2@region2@extra")
        assert "at most one @ delimiter" in str(exc_info.value)

    def test_empty_subreference_single_object_constructor(self):
        """Test that empty subreference in single object raises ValueError in constructor."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Cite2Urn(
                urn_type="cite2",
                namespace="hmt",
                collection="data",
                object_id="obj1@"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_single_object_from_string(self):
        """Test that empty subreference in single object raises ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:hmt:data:obj1@")
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_first_part_constructor(self):
        """Test that empty subreference in first range part raises ValueError in constructor."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Cite2Urn(
                urn_type="cite2",
                namespace="hmt",
                collection="data",
                object_id="obj1@-obj2"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_first_part_from_string(self):
        """Test that empty subreference in first range part raises ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:hmt:data:obj1@-obj2")
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_second_part_constructor(self):
        """Test that empty subreference in second range part raises ValueError in constructor."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Cite2Urn(
                urn_type="cite2",
                namespace="hmt",
                collection="data",
                object_id="obj1-obj2@"
            )
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_empty_subreference_range_second_part_from_string(self):
        """Test that empty subreference in second range part raises ValueError in from_string."""
        with pytest.raises(ValueError) as exc_info:
            Cite2Urn.from_string("urn:cite2:hmt:data:obj1-obj2@")
        assert "Subreference cannot be empty" in str(exc_info.value)

    def test_valid_single_subreference_single_object(self):
        """Test that a single @ sign in a single object is valid."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1"
        )
        assert urn.object_id == "obj1@region1"
        assert urn.has_subreference() is True

    def test_valid_single_subreference_range_first_part(self):
        """Test that a single @ sign in first range part is valid."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2"
        )
        assert urn.object_id == "obj1@region1-obj2"
        assert urn.has_subreference() is True

    def test_valid_single_subreference_range_second_part(self):
        """Test that a single @ sign in second range part is valid."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1-obj2@region2"
        )
        assert urn.object_id == "obj1-obj2@region2"
        assert urn.has_subreference() is True

    def test_valid_single_subreference_both_range_parts(self):
        """Test that one @ sign in each range part is valid."""
        urn = Cite2Urn(
            urn_type="cite2",
            namespace="hmt",
            collection="data",
            object_id="obj1@region1-obj2@region2"
        )
        assert urn.object_id == "obj1@region1-obj2@region2"
        assert urn.has_subreference() is True

    def test_valid_subreference_from_string_single_object(self):
        """Test that from_string accepts single @ in object."""
        urn = Cite2Urn.from_string("urn:cite2:hmt:data:obj1@region1")
        assert urn.object_id == "obj1@region1"
        assert urn.has_subreference() is True

    def test_valid_subreference_from_string_range(self):
        """Test that from_string accepts single @ in range parts."""
        urn = Cite2Urn.from_string("urn:cite2:hmt:data:obj1@region1-obj2@region2")
        assert urn.object_id == "obj1@region1-obj2@region2"
        assert urn.has_subreference() is True
