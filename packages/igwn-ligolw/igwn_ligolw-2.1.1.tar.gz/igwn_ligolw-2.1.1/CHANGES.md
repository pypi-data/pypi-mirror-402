# Changes

## 2.1.1 (2026-01-19)

- Don't install C sources in site-packages.
- Tolerate blank encoding for arrays; don't write the value of the encoding
  attribute if it is set to its default value.
- Fix crash in igwn_ligolw_no_ilwdchar.
- Build wheels for Python 3.14.
