# Documentation Consistency Checks

Rules for verifying consistency across documentation pages in the poolman project.

## Files to Inspect

- `docs/index.md` - Documentation home / overview
- `docs/getting-started.md` - Installation and setup guide
- `docs/entities.md` - Entity reference
- `docs/pool-modes.md` - Pool mode descriptions
- `docs/water-chemistry.md` - Chemistry parameter reference
- `docs/rules-and-recommendations.md` - Rule engine documentation
- `docs/contributing.md` - Contributing guide
- `README.md` - Project overview and quick start
- `zensical.toml` - Documentation site configuration (navigation)

## Check Rules

### 1. Navigation Completeness

Verify that the navigation defined in `zensical.toml` (the `nav` array) matches
the actual files in `docs/`:

- Every entry in `nav` must correspond to an existing file in `docs/`
- Every `.md` file in `docs/` should have a corresponding `nav` entry
- The page titles in `nav` should match the `#` heading in each file

### 2. Cross-Reference Accuracy

Check all internal links between documentation pages:

- Relative links in markdown (e.g. `[Entities](entities.md)`) must point to
  existing files
- Anchor links (e.g. `#section-name`) must reference existing headings in the
  target file
- The `docs/index.md` quick links section should link to every other doc page

### 3. Terminology Consistency

Verify these terms are used consistently across all doc pages and `README.md`:

| Canonical Term      | Common Variants to Flag                   |
| ------------------- | ----------------------------------------- |
| water quality score | quality score, water score, quality index |
| filtration duration | pump duration, filter duration            |
| Pool Manager        | Poolman, PoolMan, pool manager            |
| Home Assistant      | HA, home assistant, HomeAssistant         |
| ORP                 | Redox, redox potential                    |
| recommendations     | alerts, warnings, suggestions, advice     |
| pool mode           | operating mode, mode, operation mode      |
| running (mode)      | normal, active, standard                  |
| active wintering    | winter active, active winter              |
| passive wintering   | winter passive, passive winter            |

Note: abbreviated forms (like "HA" for Home Assistant) are acceptable in
parenthetical references or after first use with the full form. Flag only
when the abbreviated form is used without prior introduction on the same page.

### 4. Feature Parity Between README and Docs

The `README.md` advertises high-level features. Each one should be covered in
at least one doc page with more detail:

- "computed analytics" -> `docs/entities.md` (sensors) and `docs/water-chemistry.md`
- "rule engine with chemical dosages" -> `docs/rules-and-recommendations.md`
- "3 operational modes" -> `docs/pool-modes.md`
- "hardware agnostic" -> `docs/getting-started.md` (any sensor works)
- "multi-language" -> should be mentioned somewhere in docs

Flag any feature claimed in `README.md` that has no corresponding documentation.

### 5. Formatting Consistency

Check for consistent formatting across all doc pages:

- **Heading hierarchy**: Each page should start with a single `#` heading, then
  use `##` for sections, `###` for subsections. No skipped levels.
- **Unit formatting**: Units should be consistently formatted (e.g. "°C" not "C"
  or "degrees", "mV" not "millivolts", "ppm" not "mg/L")
- **Code formatting**: Entity IDs, config keys, and file paths should use inline
  code backticks
- **Tables**: All tables should use consistent alignment and header formatting
- **Lists**: Consistent use of `-` vs `*` for unordered lists within a page

### 6. Version and Metadata Consistency

- The version in `README.md` badges (if any) should match `manifest.json` version
- The documentation URL in `README.md` should match `manifest.json` documentation
  field and `zensical.toml` site_url
- The repository URL in `README.md` should match `manifest.json` issue_tracker
  base URL and `zensical.toml` repo_url
