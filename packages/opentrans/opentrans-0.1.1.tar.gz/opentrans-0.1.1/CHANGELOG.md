# Changelog

All notable changes to this project will be documented in this file.

## v0.1.0 - 2026-01-20

### Added
- **Initial Release**: Core engine for high-fidelity file translation.
- **Directory Preservation**: Optimized to mirror source directory structures and preserve original file extensions after translation.
- **Selective Translation**: Implemented file type filtering. Only supported extensions are translated, while all other files are copied directly to the destination.
- **Local LLM Integration**: Fully private, local-first translation powered by Ollama.
- **Syntax Shielding**: Advanced protection for JSX tags, LaTeX math, and code blocks to prevent technical syntax corruption.
- **Smart Caching**: Hash-based system to detect unchanged files and skip redundant translations, saving significant compute time.

### Known Issues
- **Complex JSX/JS in MDX**: React components or components with complex JavaScript expressions in props (e.g., `<item data={...}>`) may occasionally cause tag mismatches in Docusaurus builds.
- **Ollama Availability**: The tool requires an active Ollama instance; it does not currently auto-start the Ollama service.

### Roadmap
- [ ] Improved AST-based parsing for MDX to resolve complex JSX tag issues.
- [ ] Support for custom translation prompts via `config.yaml`.
- [ ] Automatic chunking for extremely large files.

