#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dryRun=1

cd "$ROOT_DIR"

source "$(python3 -c 'import organiseMyProjects, os; print(os.path.dirname(organiseMyProjects.__file__))')/logUtils.sh"
setApplication "myHandbook"

usage() {
    cat <<'EOF'
Usage: scripts/generateDiagrams.sh [--confirm]

Generate Mermaid SVG diagrams in handbook chapter folders.

Options:
  -y, --confirm  execute changes (default is dry-run)
  -h, --help     show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--confirm)
            dryRun=
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if ! command -v npx >/dev/null 2>&1; then
    echo "Error: npx not found. Activate the handbook conda environment first."
    exit 1
fi

node_major="$(node -p "process.versions.node.split('.')[0]")"
node_minor="$(node -p "process.versions.node.split('.')[1]")"

if [ "$node_major" -lt 18 ] || { [ "$node_major" -eq 18 ] && [ "$node_minor" -lt 19 ]; }; then
    echo "Error: Mermaid CLI requires Node 18.19 or newer. Current version: $(node --version)"
    echo "Run: conda activate handbook"
    exit 1
fi

if [[ ! -f "mermaidConfig.json" ]]; then
    echo "Error: mermaidConfig.json not found."
    exit 1
fi

mapfile -t chapter_dirs < <(
    find . -path "*/chapters" -type d -printf '%P\n' | sort
)

if [[ "${#chapter_dirs[@]}" -eq 0 ]]; then
    echo "Error: no chapter folders found."
    exit 1
fi

found_diagrams=0
generated_diagrams=0
skipped_diagrams=0

log_doing "diagram generation"
log_value "dryRun" "${dryRun:-0}"

while IFS= read -r -d '' input; do
    found_diagrams=1
    output="${input%.mmd}.svg"

    if [[ -f "$output" && ! "$input" -nt "$output" ]]; then
        log_info "skipping current: $output"
        skipped_diagrams=$((skipped_diagrams + 1))
        continue
    fi

    log_action "generate diagram: $output"

    if [[ -z "${dryRun:-}" ]]; then
        npx mmdc \
            -i "$input" \
            -o "$output" \
            -c "mermaidConfig.json"
    fi

    generated_diagrams=$((generated_diagrams + 1))
done < <(find "${chapter_dirs[@]}" -type f -name "*.mmd" -print0)

if [[ "$found_diagrams" -eq 0 ]]; then
    log_info "no Mermaid diagrams found in chapter folders"
fi

log_value "generated" "$generated_diagrams"
log_value "skipped" "$skipped_diagrams"
log_done "diagram generation"

echo "Done. Generated: $generated_diagrams. Skipped: $skipped_diagrams."
