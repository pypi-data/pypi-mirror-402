# rsm-markup → rsm-lang

**This package has been renamed to `rsm-lang`.**

## Migration

Please update your installation:

```bash
# Old (deprecated)
pip install rsm-markup

# New (current)
pip install rsm-lang
```

## Why the rename?

RSM (Readable Science Markup) is a **language** for semantic research publishing, not just a markup format. The new name better reflects its capabilities:

- Semantic research constructs (hypothesis, protocol, limitation, assumption)
- Claim/evidence linking
- Sophisticated numbering systems
- Research-native features

The `rsm` CLI command remains the same.

## What happens now?

Installing `rsm-markup` will automatically install `rsm-lang` as a dependency. This ensures backward compatibility for existing projects.

However, we recommend updating to `rsm-lang` directly:

```bash
pip uninstall rsm-markup
pip install rsm-lang
```

Or if using `uv`:

```bash
uv remove rsm-markup
uv add rsm-lang
```

## Learn More

- [RSM Website](https://write-rsm.org/)
- [RSM Documentation](https://docs.write-rsm.org/)
- [GitHub Repository](https://github.com/leotrs/rsm)

---

**Note**: This is a redirect package. All development happens in `rsm-lang`.
