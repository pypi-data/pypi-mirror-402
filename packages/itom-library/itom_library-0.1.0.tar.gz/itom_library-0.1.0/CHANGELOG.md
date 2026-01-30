# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-08

### Added
- Initial release
- `OOClient` class for interacting with OpenText Operations Orchestration with CSRF token support authentication
- Reseponse format options: JSON and table
- `get_flows()` method to retrieve all flows from the library
- `get_flow_inputs(flow_id)` method to retrieve inputs for a specific flow

- Custom exceptions: `OOClientError`, `OOAuthenticationError`, `OOAPIError`
- Full type hints support