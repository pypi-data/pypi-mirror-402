# Mylonics MkDocs Theme

A custom MkDocs Material theme override for Mylonics documentation sites.

## Features

- Custom K2D font branding for header
- Styled header with gray color scheme
- SEO optimizations (Open Graph, Twitter Cards, structured data)
- Clean minimal design matching mylonics.com

## Usage

### As a Git Submodule

Add this theme to your MkDocs project as a submodule:

```bash
git submodule add https://github.com/mylonics/mylonics-mkdocs-theme docs/theme_overrides
```

Then in your `mkdocs.yml`:

```yaml
theme:
  name: material
  custom_dir: docs/theme_overrides
```

### Updating the Theme

To update to the latest version:

```bash
git submodule update --remote docs/theme_overrides
```

### Cloning a Project with this Submodule

When cloning a project that uses this theme:

```bash
git clone --recurse-submodules <your-repo-url>
```

Or if already cloned:

```bash
git submodule init
git submodule update
```

## Customization

The theme extends Material for MkDocs with these overrides:

- `main.html` - Custom meta tags, fonts, and SEO structured data
- `partials/header.html` - Custom header with page.title display
- `assets/stylesheets/extra.css` - Custom styling

## Requirements

- MkDocs >= 1.5.0
- mkdocs-material >= 9.0.0

## License

MIT License - Copyright (c) 2025 Mylonics
