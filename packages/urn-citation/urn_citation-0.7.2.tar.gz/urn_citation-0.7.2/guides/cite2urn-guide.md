# User's Guide to the `Cite2Urn` class

### Creating a Cite2Urn



#### Parsing from a string

```python
# Parse a URN string
urn = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:codexmodel")
```
#### Using the constructor

```python
from urn_citation import Cite2Urn

# Basic URN
urn = Cite2Urn(urn_type="cite2", namespace="hmt", collection="datamodels")

# With version and object
urn = Cite2Urn(
    urn_type="cite2",
    namespace="hmt",
    collection="datamodels",
    version="v1",
    object_id="codexmodel"
)
```



### Working with Objects

Cite2Urns can identify either single objects ranges of objects if the collection is an ordered collection. In the case of a range, the object component will have a hyphen separator:

```python
urn = Cite2Urn.from_string("urn:cite2:hmt:data:obj1-obj2")

# Check if object is a range
if urn.is_range():
    start = urn.range_begin()  # "obj1"
    end = urn.range_end()      # "obj2"
```

### Comparing URNs

#### Collection comparisons

Compare the collection hierarchy (namespace, collection, version):

```python
urn1 = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:obj1")
urn2 = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:obj2")

# Are collection hierarchies identical?
urn1.collection_equals(urn2)  # True

# Does urn1's collection hierarchy contain urn2's?
urn1.collection_contains(urn2)  # True

# With partial constraints
urn3 = Cite2Urn(urn_type="cite2", namespace="hmt", collection="datamodels")
urn3.collection_contains(urn1)  # True (only namespace and collection constrained)
```

#### Object comparisons

```python
urn1 = Cite2Urn.from_string("urn:cite2:hmt:data:obj1")
urn2 = Cite2Urn.from_string("urn:cite2:hmt:data:obj2")

# Are objects identical?
urn1.object_equals(urn2)  # False

urn3 = Cite2Urn.from_string("urn:cite2:hmt:data:obj1")
urn1.object_equals(urn3)  # True
```

#### Full URN containment

```python
# urn1 contains urn2 and their object components are identical
urn1.contains(urn2)
```

### Modifying URNs

Create new URNs with modified components:

```python
urn = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:obj1")

# Drop components
urn.drop_version()    # Returns URN without version
urn.drop_objectid()   # Returns URN without object_id
```

### String Serialization

```python
urn = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:obj1")

# Convert back to string
urn_string = str(urn)  # "urn:cite2:hmt:datamodels.v1:obj1"
```

## Validation

Both classes provide validation methods to check if a string is valid before parsing:

```python
# Check if string is a valid CTS URN
if CtsUrn.valid_string("urn:cts:greekLit:tlg0012:1.1"):
    urn = CtsUrn.from_string("urn:cts:greekLit:tlg0012:1.1")

# Check if string is a valid CITE2 URN
if Cite2Urn.valid_string("urn:cite2:hmt:datamodels.v1:obj1"):
    urn = Cite2Urn.from_string("urn:cite2:hmt:datamodels.v1:obj1")
```
## Summary of CITE2 URN String Format
```
urn:cite2:<namespace>:<collection_info>:<object>

collection_info: <collection>[.<version>]
object:          <id>[-<id>]  (single or range)
```

Example: `urn:cite2:hmt:datamodels.v1:codexmodel`
