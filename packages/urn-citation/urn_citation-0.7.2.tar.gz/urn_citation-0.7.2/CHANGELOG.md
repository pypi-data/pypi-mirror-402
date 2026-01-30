# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 0.7.1 - 2026-01-21

No changes to python code; only documentation updates.

### Added

- automated build of API documentation using MkDocs and mkdocstrings.
- automated publication of current API documentation to GitHub Pages upon commits to the main branch.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.7.0...v0.7.1).



## 0.7.0 - 2026-01-21

### Added

- `drop_subreference` methods on both `CtsUrn` and `Cite2Urn` classes to create a new URN without any subreference components.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.6.0...v0.7.0).



## 0.6.0 - 2026-01-21

### Added

Support for working with subreferences on CTS URNs and CITE2 URNs:

- methods to parse, validate, and retrieve subreferences.
- unit tests for all functionality related to subreferences.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.5.0...v0.6.0).


## 0.5.0 - 2026-01-16

### Added

- `Cite2Urn` class to represent and manipulate CITE2 URNs.
- Methods for parsing, validating, and formatting CITE2 URNs.
- Unit tests for all functionalities of the `Cite2Urn` class.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.4.1...v0.5.0).



## 0.4.1 - 2026-01-15

Addresses a gap in validation logic for instantiating the `CtsUrn` class.

### Fixed

- Added validation to ensure that neither `exemplar` nor `version` can be set when higher elements of the work hierarchy are `None`.


For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.4.0...v0.4.1).



## 0.4.0 - 2026-01-15

Non-breaking additions to the `CtsUrn` class.

### Added

- `drop_passage` method to create a new `CtsUrn` without the passage component.
- `set_passage` method to create a new `CtsUrn` with a specified passage component.
- `drop_version` method to create a new `CtsUrn` without the version component.
- `set_version` method to create a new `CtsUrn` with a specified version component.
- `drop_exemplar` method to create a new `CtsUrn` without the exemplar component.
- `set_exemplar` method to create a new `CtsUrn` with a specified exemplar component.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.3.0...v0.4.0).


## 0.3.0 - 2026-01-15

Breaking changes to the `CtsUrn` class.

### Added

- `passage_contains` method to check if one passage is contained within another. Replaces the previous `passage_similar` method.
- `work_contains` method to check if one passage is contained within another. Replaces the previous `work_similar` method.
- `contains` method to check if one passage is contained within another. Replaces the previous `urn_similar` method.

### Changed

- Updated unit tests to reflect the new containment methods and removal of the old similarity methods.


### Removed

- `passage_similar`, `work_similar`, and `urn_similar` methods from `CtsUrn` class as they have been replaced by the new containment methods.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.2.0...v0.3.0).


## 0.2.0 - 2026-01-14

Breaking changes to the `CtsUrn` class.  



### Added

- `__str__` method implemented for `CtsUrn` class to provide a string representation of the URN.

### Changed

- Updated unit tests to reflect the addition of the `__str__` method and deletion of `to_string` method.

### Removed

- `to_string` method from `CtsUrn` class as it is redundant with the new `__str__` method.

For more details, see the [complete diff](https://github.com/neelsmith/urn_citation/compare/v0.1.0...v0.2.0).


## 0.1.0 - 2026-01-13 

[Initial release](https://github.com/neelsmith/urn_citation/releases/tag/v0.0.1).

### Added

- `CtsUrn` class to represent and manipulate CTS URNs.
- Methods for parsing, validating, and formatting CTS URNs.
- Unit tests for all functionalities of the `CtsUrn` class.

