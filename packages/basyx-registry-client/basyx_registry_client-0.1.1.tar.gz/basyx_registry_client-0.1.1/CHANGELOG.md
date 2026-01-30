# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-01-22

### Added

- Docker support with Dockerfile for containerized usage
- GitHub Container Registry (GHCR) workflow for automatic Docker image publishing
- Release asset uploads (wheel and sdist) to GitHub releases

### Fixed

- Hatchling wheel build configuration for Docker compatibility

## [0.1.0] - 2026-01-22

### Added

- Synchronous and asynchronous registry clients
- Descriptor models for AAS, Submodels, and endpoints
- Base64url encoding helpers for identifier paths
- Endpoint resolver with HTTPS preference on fallback
- Optional basyx-client integration helper
- Tests for core behavior and HTTP interactions
