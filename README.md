# My Handbook

A personal knowledge repository containing coaching manuals, reference manuals, notes and supporting material.

The aim is not to create formal publications. The aim is to keep practical documents in a consistent structure so they are easy to return to, improve and reuse.

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
- [FM Parser Samples](fmparser/samples/README.md)
- [Templates Changelog](templates/CHANGELOG.md)

## Current Areas

- Football Manager Coaching Manual
- Walking Football Coaching Manual
- Linux Reference Manual

## Repository Structure

```text
templates/          Shared LibreOffice template and template assets
documentation/      Living project guides and planning notes
football-manager/   Football Manager coaching manual and supporting material
walking-football/   Walking football coaching manual, drills and diagrams
linux/              Linux reference manual, notes and scripts
shared/             Shared icons, images and diagrams
scripts/            Safe-by-default maintenance scripts
```

## Working Standard

All manuals should use the shared LibreOffice template in `templates/`.

The preferred workflow is:

1. Draft or refine the content.
2. Paste into the LibreOffice document.
3. Let the template styles do the formatting.
4. Export final PDFs into the relevant `exports/` folder when needed.

The template should do the work. If repeated manual style changes are needed, improve the template rather than accepting the extra step.
