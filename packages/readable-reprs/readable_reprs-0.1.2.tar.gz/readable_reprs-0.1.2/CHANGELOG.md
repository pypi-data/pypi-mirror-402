# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.2 - 2026-01-18

### Changed

- `enum.Enum` patch now preserves introspectability (e.g. `__repr__.__module__` is 'enum', as it is without the patch).

## 0.1.1 - 2026-01-11

### Fixed

- Publishing accidentally included an empty SBOM.

## 0.1.0 - 2026-01-10

### Added

- `patch_reprs` function, supporting `enum.Enum`.
