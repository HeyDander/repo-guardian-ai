# Changelog

## 0.4.0 - 2026-08-25

- Added dependency-free interactive terminal dashboard via `repo-guardian ui`.
- Added Overview, Findings and Codebase Map screens with keyboard navigation.
- Added score bars, severity colors, refresh and terminal-friendly layout.

## 0.3.3 - 2026-08-25

- Reduced security false positives for documented configuration placeholders.

## 0.3.2 - 2026-08-25

- Kept empty-diff review notices in explicit `review` mode instead of full health reports.
- Ignored documented secret placeholders such as `YOUR_PASSWORD` in security findings.

## 0.3.1 - 2026-08-25

- Reduced false positives by excluding test/fixture code from production stack, architecture and performance signals.
- Avoided lockfile warnings for Python projects without runtime dependencies.
- Added regression coverage for fixture-only stack markers.

## 0.3.0 - 2026-08-25

- Added Strict Engineer Contract for scope control, evidence and verification gates.
- Added explicit `NOT RUN` and minimal-patch rules for AI coding agents.
- Added contract regression tests and documented strict behavior in README.

## 0.2.0 - 2026-08-25

- Added dependency manifest/lockfile checks and version-range warnings.
- Added conservative performance, architecture, release and Git diff analyzers.
- Added behavior tests for the new modes and corrected mode routing.

## 0.1.0 - 2026-08-25

- Initial portable Skill and provider-neutral CLI.
- Evidence-based security, test, quality and documentation analyzers.
- Stack detection, score explanation, JSON output and safety boundaries.
