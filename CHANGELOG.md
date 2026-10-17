# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-17

### Added

- Text extraction as Markdown from PDF and images (PNG, JPG, WEBP, GIF, BMP, TIFF) with a vision model
- Page markers for PDFs, can be turned off
- Limits for file size, page count and image size with clear error messages
- Oversized images are downscaled before sending
- Command-line tool with output to file, folder or stdout
- Python API (`extract`, `extract_many`)
- Works with any OpenAI-compatible server, with or without an API key

[Unreleased]: https://github.com/hamidmergan/doc-extract/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hamidmergan/doc-extract/releases/tag/v0.1.0
