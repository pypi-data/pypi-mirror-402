# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-19

### Added

- Initial release of the Burki Python SDK
- Full API coverage for all Burki resources:
  - **Assistants**: Create, update, delete, list, and configure AI voice assistants
  - **Calls**: Initiate outbound calls, list calls, get transcripts, recordings, and metrics
  - **Phone Numbers**: Search, purchase, release, and manage phone numbers across providers (Twilio, Telnyx, Vonage)
  - **SMS**: Send messages, manage conversations, and track delivery status
  - **Campaigns**: Create and manage outbound calling campaigns with progress tracking
  - **Documents**: Upload and manage knowledge base documents for RAG
  - **Tools**: Create and manage custom tools (HTTP, Python, Lambda)
- Real-time WebSocket support:
  - Live transcript streaming during calls
  - Campaign progress monitoring
- Async/await support for all API methods (`*_async` variants)
- Comprehensive error handling with typed exceptions
- Full type hints and PEP 561 compliance
- Pydantic v2 models for request/response validation
