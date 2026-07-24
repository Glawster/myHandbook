# Walking Football Session Builder

The session builder produces LibreOffice Writer documents from YAML while keeping
the ODT template in control of all formatting.

```text
templates/sessionTemplate.odt + sessions/*.yaml
                    ↓
                 main.py
                    ↓
              generated/*.odt
```

## Requirements

- Python 3.10 or newer
- `lxml`
- `PyYAML`
- `organiseMyProjects` (the repository-standard logging package)

The builder modifies only `content.xml`. Every other template package member,
including styles, headers, images, settings and manifests, is copied and verified
byte-for-byte.

## Template placeholders

The supported placeholders are:

```text
{{sessionTitle}}  {{theme}}           {{keyPhrase}}
{{duration}}      {{players}}         {{equipment}}
{{objectives}}    {{warmup}}          {{drill1}}
{{drill2}}        {{drill3}}          {{matchPractice}}
{{coolDown}}      {{coachingPoints}}  {{commonMistakes}}
{{analysis}}      {{sessionSummary}}  {{nextSession}}
```

LibreOffice may split a placeholder across styled spans; the renderer handles that
without removing those spans. A placeholder must remain within one paragraph or
heading. YAML list values produce ODF line breaks and inherit the placeholder's
formatting.

## Usage

Preview and validate the default build:

```bash
python3 walking-football/main.py
```

Generate the documents:

```bash
python3 walking-football/main.py --confirm
```

Custom paths are supported with `--template`, `--source` and `--output`.
Generated documents are intentionally excluded from version control.

## Tests

```bash
pytest walking-football/tests
```
