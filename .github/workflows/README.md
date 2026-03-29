# Release workflow notes

This repo uses `.github/workflows/release.yml`.

Versioning rule based on the latest commit subject on `main`:

- `feat:` -> bump **major** (`x.0.0 -> x+1.0.0`)
- `fix:` -> bump **minor** (`x.y.0 -> x.y+1.0`)
- anything else, including `chore:` -> bump **patch** (`x.y.z -> x.y.z+1`)

Examples:

- `feat: add evaluator batching` -> `1.2.3` becomes `2.0.0`
- `fix: handle empty listing export` -> `1.2.3` becomes `1.3.0`
- `chore: tidy readme` -> `1.2.3` becomes `1.2.4`

Notes:

- The workflow runs on pushes to `main`.
- It creates a release commit and a git tag like `v1.2.3`.
- It publishes to npm using `NPM_TOKEN`.
- Commits created by the workflow include `[skip ci]` to avoid loops.

Required GitHub secret:

- `NPM_TOKEN` - npm token allowed to publish this package
