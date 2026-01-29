# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-01-20

### Added
- **Analisi Prezzi tools** (5 new tools)
  - `leeno_analisi_create` - Create new price analysis
  - `leeno_analisi_add_componente` - Add component to analysis
  - `leeno_analisi_transfer` - Transfer analysis to Elenco Prezzi
  - `leeno_analisi_list` - List all price analyses
  - `leeno_analisi_create_complete` - Create complete analysis with components

- **Import Prezzari tools** (4 new tools)
  - `leeno_prezzi_import` - Import price list from XML file
  - `leeno_prezzi_detect_format` - Detect price list format
  - `leeno_prezzi_list_formats` - List supported formats
  - `leeno_prezzi_import_url` - Import price list from URL
  - Supported regional formats: Toscana, Lombardia, Veneto, Liguria, Sardegna, Basilicata, Calabria, Campania, SIX, XPWE

- **Varianti tools** (4 new tools)
  - `leeno_variante_create` - Create project variant from COMPUTO
  - `leeno_variante_info` - Get variant information
  - `leeno_variante_compare` - Compare VARIANTE vs COMPUTO
  - `leeno_variante_delete` - Delete variant

- **Giornale Lavori tools** (5 new tools)
  - `leeno_giornale_create` - Create work diary
  - `leeno_giornale_nuovo_giorno` - Add new day entry
  - `leeno_giornale_info` - Get diary information
  - `leeno_giornale_list_giorni` - List all day entries
  - `leeno_giornale_add_nota` - Add note to day entry

- Cross-platform LeenO path auto-detection
  - Support for Windows, Linux, and macOS
  - Auto-detect from LibreOffice extensions folder
  - Environment variables: `LEENO_PYTHONPATH`, `LEENO_PATH`

- GitHub Actions CI/CD workflows
- CHANGELOG.md following Keep a Changelog format
- pytest-cov for test coverage

### Changed
- Updated version from 0.1.0 (Alpha) to 0.5.0 (Beta)
- Development status changed to Beta
- Added upper bounds to dependencies (mcp<2.0.0, pydantic<3.0.0)
- Improved pyproject.toml with URLs and additional metadata

### Fixed
- Removed hardcoded LeenO path (was Windows-specific)
- Path detection now works on all platforms

## [0.1.0] - 2025-01-20

### Added
- Initial release with 32 MCP tools
- **Document tools** (6): create, open, save, close, list, info
- **Computo tools** (8): add_voce, list_voci, get_voce, delete_voce, add_capitolo, add_misura, get_totale, get_struttura
- **Elenco Prezzi tools** (7): search, get, add, edit, delete, list, count
- **Contabilità tools** (6): add_voce, list_voci, get_sal, get_stato, emetti_sal, annulla_sal
- **Export tools** (5): pdf, csv, xlsx, xpwe, formats
- UNO Bridge for LibreOffice connection
- Document pool for managing multiple documents
- LeenO macros integration
- Pydantic models for data validation
- 112 unit tests with UNO mocking
- Multi-platform support (Windows, Linux, macOS)
- Claude Desktop and Claude Code configuration examples

[0.5.0]: https://github.com/mikibart/leeno-mcp-server/compare/v0.1.0...v0.5.0
[0.1.0]: https://github.com/mikibart/leeno-mcp-server/releases/tag/v0.1.0
