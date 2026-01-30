# User's Guide to the `CtsUrn` class


### Creating a CtsUrn

#### Parsing from a string

```python
# Parse a URN string
urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012.001.wacl1.ex1:1.1-1.5")
```


#### Using the constructor

```python
from urn_citation import CtsUrn

# Basic URN with just required fields
urn = CtsUrn(urn_type="cts", namespace="greekLit", text_group="tlg0012")

# Full URN with all hierarchy levels
urn = CtsUrn(
    urn_type="cts",
    namespace="greekLit",
    text_group="tlg0012",
    work="001",
    version="wacl1",
    exemplar="ex1",
    passage="1.1"
)
```

### Working with Passages

Passages may be single identifiers or ranges (with a hyphen separator):

```python
urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012:1.1-1.5")

# Check if passage is a range
if urn.is_range():
    start = urn.range_begin()  # "1.1"
    end = urn.range_end()      # "1.5"
```

### Comparing CTS URNs with URN logic

#### Comparing work hierarchies

Compare the work hierarchy (namespace, text_group, work, version, exemplar):

```python
urn1 = CtsUrn.from_string("urn:cts:greekLit:tlg0012.001:1.1")
urn2 = CtsUrn.from_string("urn:cts:greekLit:tlg0012.001:1.5")

# Are work hierarchies identical?
urn1.work_equals(urn2)  # True

# Does urn1's work hierarchy contain urn2's?
urn1.work_contains(urn2)  # True

# With partial constraints
urn3 = CtsUrn(urn_type="cts", namespace="greekLit", text_group="tlg0012")
urn3.work_contains(urn1)  # True (only namespace and text_group constrained)
```

#### Passage comparisons


`passage_contains` raises ValueError if either passage is a range: to compare ranges of passages, you need access to the full corpus of the text, not just a URN.  See `citable_corpus` for this functionality.  The `passage_equals` method can be used to compare passages without this context, but it will only return True if the passages are identical strings (e.g., "1" does not equal "1.1").


```python
urn1 = CtsUrn.from_string("urn:cts:greekLit:tlg0012:1")
urn2 = CtsUrn.from_string("urn:cts:greekLit:tlg0012:1.1")

# Are passages identical?
urn1.passage_equals(urn2)  # False

# Does passage "1" contain refinement "1.1"?
urn1.passage_contains(urn2)  # True
```

#### Full URN containment

```python
# Check if this URN fully contains another (work AND passage)
urn1.contains(urn2)
```

### Modifying URNs

Create new URNs with modified components:

```python
urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012.001.wacl1.ex1:1.1")

# Drop components
urn.drop_version()    # Returns URN without version (and exemplar)
urn.drop_passage()    # Returns URN without passage
urn.drop_exemplar()   # Returns URN without exemplar

# Set new values
urn.set_version("wacl2")   # Returns URN with new version
urn.set_passage("2.1-2.5") # Returns URN with new passage
urn.set_exemplar("ex2")    # Returns URN with new exemplar
```

### String Serialization

```python
urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012.001.wacl1:1.1")

# Convert back to string
urn_string = str(urn)  # "urn:cts:greekLit:tlg0012.001.wacl1:1.1"
```


## Summary of CTS URN String Format
```
urn:cts:<namespace>:<work_hierarchy>:<passage>

work_hierarchy:  <text_group>[.<work>[.<version>[.<exemplar>]]]
passage:         <passage>[- <passage>]  (single or range)
```

Example: `urn:cts:greekLit:tlg0012.001.wacl1.ex1:1.1-1.5`

