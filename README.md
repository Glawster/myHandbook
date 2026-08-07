# My Handbook

A personal knowledge repository containing coaching manuals, reference manuals, notes and
supporting tools.

The aim is not to create formal publications. The aim is to keep practical documents in a
consistent structure so they are easy to return to, improve and reuse.

## Documentation

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Reverse Engineering Notes](documentation/reverseEngineering.md)
- [FM26 Skin Bundle Explorer](documentation/skinBundleExplorer.md)
- [FMParser Core Architecture](documentation/fmparserArchitecture.md)
- [FMParser Automation Framework](documentation/automationFramework.md)
- [Reverse Engineering Notes](documentation/reverseEngineering.md)
- [Roadmap](documentation/roadmap.md)
- [Style Guide](documentation/styleGuide.md)
- [Volume 1 Editorial Plan](documentation/volume1EditorialPlan.md)
- [FMSAT Samples](fmsat/samples/README.md)
- [Football Manager Squad Assessment Tool](fmsat/README.md)
- [Templates Changelog](templates/CHANGELOG.md)
- [Walking Football Session Builder](walking-football/README.md)

## Current Areas

- Football Manager Coaching Manual
- Walking Football Coaching Manual
- Linux Reference Manual

## Tools

### Football Manager Squad Assessment Tool (FMSAT)

[FMSAT](fmsat/README.md) is a local desktop application for extracting structured player
data from Football Manager screenshots. Phase 1 supports the Squad Attributes screen and
stores user-confirmed results in SQLite. It does not modify Football Manager or read save
files. The same package also contains the repository's existing `.fmf` inspection and
comparison utilities, available through the `fmsat parser` command.

## Repository Structure

```text
templates/          Shared LibreOffice template and template assets
documentation/      Living project guides and planning notes
football-manager/   Football Manager coaching manual and supporting material
walking-football/   Walking Football coaching manual, drills and diagrams
linux/              Linux reference manual, notes and scripts
shared/             Shared icons, images and diagrams
scripts/            Safe-by-default maintenance scripts
fmsat/              Football Manager parsing and screenshot assessment tools
```

## Working Standard

All manuals should use the shared LibreOffice template in `templates/`.

The preferred workflow is:

1. Draft or refine the content.
2. Paste into the LibreOffice document.
3. Let the template styles do the formatting.
4. Export final PDFs into the relevant `exports/` folder when needed.

The template should do the work. If repeated manual style changes are needed, improve the
template rather than accepting the extra step.
