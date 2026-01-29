## [v0.2.2](https://pypi.org/project/amsdal_ml/0.2.2/) - 2026-01-19

### Fixed

- Added support for `JSON_SCHEMA` response format when using attachments in OpenAI Responses API.
- Support for images in OpenAI Responses API (automatically selects `input_image` based on MIME type).
- Added `mime_type` support to `FileAttachment` and `OpenAIFileLoader`.
