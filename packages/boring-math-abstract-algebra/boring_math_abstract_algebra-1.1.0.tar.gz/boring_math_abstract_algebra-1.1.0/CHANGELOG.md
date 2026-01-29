# CHANGELOG

PyPI pythonic-fp-protocols project.

## Semantic Versioning

Strict 3 digit semantic versioning.

- **MAJOR** version incremented for incompatible API changes
- **MINOR** version incremented for backward compatible added functionality
- **PATCH** version incremented for backward compatible bug fixes

See [Semantic Versioning 2.0.0](https://semver.org).

## Releases and Important Milestones

### Released PyPI version 1.1.0 - 2026-01-17

Narrowed focus to just concrete representations of algebras.

Decided to take a break from abstract algebra for a while. New algebra
efforts will likely be done in new PyPI projects.

### Released PyPI version 0.1.0 - 2025-12-01

Suspect I am off with my test dependencies in pyproject.toml

### Update - 2025-11-08

- elements
  - elements know the concrete algebra to which they belong
  - they wrap hashable immutable representations
  - binary operations like * and + can act on the elements
    - not their representations
- algebras
  - contain a dict of their potential elements
    - can be used with potentially infinite or continuous algebras
    - the dict is "quasi-immutable"
      - elements are added in a "natural" uniquely deterministic way
  - contain user defined functions and attributes
    - functions take representation valued parameters and return values
    - attributes are ``ref`` valued

### Update - 2025-10-17

Major increase in my understanding of Protocols.

- decided to move project to Boring Math
- renaming repo pythonic-fp-protocols -> boring-math-abstract-algebra

### Update - 2025-10-13

Narrowing scope of project to just protocols.

- renaming repo to pythonic-fp-protocols
- began work on module pythonic-fp-protocols.algebraic

### Created  - 2025-10-12

Created GitHub repo pythonic-fp-typing for a future PyPI project of that
name.
