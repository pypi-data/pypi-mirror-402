# GitHub Workflows

## PyPI Release

Publishes GitHub Releases to PyPI via trusted publishing. Publishes release-candidates (tagged with `v*rc*`) pushed from the CLI to TestPyPI.

### Expected Behavior
* Push a new tag (e.g., `v1.2.3-rc1`) &rarr; publishes to TestPyPI
* Create a GitHub Release with a `v*rc*` tag (e.g., `v1.2.3-rc1`) &rarr; publishes to TestPyPI
* Create a GitHub Release with a `v*` tag that is **not** marked for pre-release (no `*rc*`) &rarr; publishes to PyPI
* Create a GitHub Release for a `v*rc*` tag (even if not marked as pre-release) &rarr; blocked from PyPI by safeguard.