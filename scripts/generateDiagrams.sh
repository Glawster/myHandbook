#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

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

if [ ! -f "mermaidConfig.json" ]; then
    echo "Error: mermaidConfig.json not found."
    exit 1
fi

mapfile -t volume_dirs < <(
    find . -maxdepth 1 -type d -regextype posix-extended -regex './Volume [0-9]+' -printf '%P\n' | sort -V
)

if [ "${#volume_dirs[@]}" -eq 0 ]; then
    echo "Error: no Volume folders found."
    exit 1
fi

found_diagrams=0

while IFS= read -r -d '' input; do
    found_diagrams=1
    output="${input%.mmd}.svg"

    echo "Generating: $output"

    npx mmdc \
        -i "$input" \
        -o "$output" \
        -c "mermaidConfig.json"
done < <(find "${volume_dirs[@]}" -type f -name "*.mmd" -print0)

if [ "$found_diagrams" -eq 0 ]; then
    echo "No Mermaid diagrams found in Volume folders."
fi

echo "Done."
