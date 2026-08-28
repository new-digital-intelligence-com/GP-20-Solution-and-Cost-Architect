#!/usr/bin/env bash
# Render the GP-20 process flow to a high-resolution PNG.
#
#   ./render_diagram.sh [width_px]     default 3000
#
# Requires: plantuml (with graphviz), rsvg-convert (librsvg2-bin)
#   Debian/Ubuntu:  apt-get install plantuml graphviz librsvg2-bin
#   macOS:          brew install plantuml librsvg
#   Windows:        choco install plantuml   (and use Inkscape for the SVG->PNG step)
#
# PlantUML's own -tpng output is bitmap-scaled and soft. Going via SVG and
# rasterising at an explicit width gives crisp text at any size.
#
# NOTE ON FILENAMES: the source is process_flow.puml, but the opening directive
# inside it names the diagram GP20_Process_Flow, and PlantUML names its OUTPUT
# after the diagram, not after the source file. So the SVG is
# GP20_Process_Flow.svg. Looking for process_flow.svg and concluding the render
# failed has cost real time before now.

set -euo pipefail
cd "$(dirname "$0")"

WIDTH="${1:-3000}"
SRC="process_flow.puml"
SVG="GP20_Process_Flow.svg"
PNG="GP20_Process_Flow.png"

command -v plantuml >/dev/null || { echo "plantuml not found"; exit 1; }

echo "Rendering $SRC -> $SVG"
rm -f "$SVG" "$PNG"
plantuml -tsvg "$SRC"
[ -f "$SVG" ] || { echo "expected $SVG — check the diagram name in $SRC"; exit 1; }

# A <size:n> or <b> tag that opens and closes on different physical lines leaks
# its literal closing tag into the picture. Cheap to check, easy to miss by eye.
if grep -q "&lt;/size&gt;\|&lt;/b&gt;\|&lt;/color&gt;" "$SVG"; then
    echo "WARNING: a literal closing tag leaked into the diagram."
    echo "         A style tag must open and close on the same physical line."
fi

if command -v rsvg-convert >/dev/null; then
    rsvg-convert -w "$WIDTH" -a --background-color=white "$SVG" -o "$PNG"
elif command -v inkscape >/dev/null; then
    inkscape "$SVG" --export-type=png --export-filename="$PNG" --export-width="$WIDTH"
elif command -v magick >/dev/null; then
    magick -density 300 -background white "$SVG" -resize "${WIDTH}x" "$PNG"
else
    echo "No SVG rasteriser found (rsvg-convert / inkscape / magick)."
    echo "The SVG is written and is vector — use it directly in slides."
    exit 0
fi

echo "Written: $PNG (${WIDTH}px wide)  and  $SVG (vector, for slides)"
