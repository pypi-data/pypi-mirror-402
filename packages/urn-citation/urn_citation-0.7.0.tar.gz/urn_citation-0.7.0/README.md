# `urn_citation`

A Python library for working with CITE architecture URNs for scholarly citation.


## Overview

`urn_citation` provides Pydantic-based models for representing and parsing Uniform Resource Names (URNs) defined for the CITE architecture. The current release supports Canonical Text Service (CTS) URNs, which are used to identify passages of canonically citable texts with hierarchical work and passage components.

## Features

- **Pydantic Models**: Type-safe URN representations with validation
- **CTS URN Support**: Full support for parsing and creating Canonical Text Service URNs
- **Flexible Parsing**: Parse CTS URN strings into structured objects
- **Optional Fields**: Support for optional work, version, exemplar, and passage components

## Installation

```bash
pip install urn-citation
```

## Quick Start

### Creating a CTS URN

```python
from urn_citation import CtsUrn

# Create a CTS URN with required fields
urn = CtsUrn(
    urn_type="cts",
    namespace="greekLit",
    text_group="tlg0012"
)

# Create a CTS URN with all fields
urn_full = CtsUrn(
    urn_type="cts",
    namespace="greekLit",
    text_group="tlg0012",
    work="001",
    version="wacl1",
    exemplar="ex1",
    passage="1.1-1.5"
)
```

### Parsing from a String

```python
# Parse a CTS URN from a colon-delimited string
urn_string = "urn:cts:greekLit:tlg0012.001.wacl1:1.1-1.5"
urn = CtsUrn.from_string(urn_string)

print(urn.text_group)  # "tlg0012"
print(urn.work)        # "001"
print(urn.version)     # "wacl1"
print(urn.passage)     # "1.1-1.5"
```

### Serialization

```python
# Convert to dictionary
urn_dict = urn.model_dump()

# Convert to JSON
urn_json = urn.model_dump_json()
```

## CTS URN Structure

A CTS URN follows the format:

```
urn:cts:<namespace>:<work_component>:<passage_component>
```

Where:
- **namespace**: The namespace defining the text collection (e.g., "greekLit", "latinLit")
- **work_component**: One to four dot-delimited identifiers for text group, work, version, and exemplar
- **passage_component**: Optional passage reference, may contain a single passage or range (with hyphen)


## License

See the LICENSE file for details.