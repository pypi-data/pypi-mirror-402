# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SVGDiagram is a C++20 library for rendering diagrams to SVG. It provides manual layout of nodes and edges (no automatic layout). The library is available as:
- A native C++ static library
- A Python package (`sp-svg-diagram`) via pybind11
- An npm package (`sp-svg-diagram`) via WebAssembly/Emscripten

## Build Commands

### C++ (CMake)

```bash
# Configure with tests enabled
cmake -B build -DSVG_DIAGRAM_ENABLE_TESTS=ON

# Build
cmake --build build

# Run tests
cd build && ctest --output-on-failure
```

CMake options:
- `-DSVG_DIAGRAM_ENABLE_TESTS=ON` - Enable C++ tests (uses GoogleTest)
- `-DSVG_DIAGRAM_ENABLE_PANGO_CAIRO=ON` - Enable accurate text measurement with PangoCairo
- `-DSVG_DIAGRAM_ENABLE_COVERAGE=ON` - Enable coverage reporting
- `-DSVG_DIAGRAM_ENABLE_STRICT=ON` - Enable strict compiler warnings
- `-DSVG_DIAGRAM_BIND_PYTHON=ON` - Build Python bindings
- `-DSVG_DIAGRAM_BIND_ES=ON` - Build WASM/ES bindings

### Python

```bash
# Install in development mode with test dependencies
pip install -e ".[test]"

# Run tests
pytest -v python/tests

# Linting
black --check python/wrapper python/tests
isort --check-only python/wrapper python/tests
flake8 --max-line-length=120 python/wrapper python/tests
```

### WASM/JavaScript

```bash
cd wasm

# Build (requires Emscripten SDK in PATH)
npm run build  # or: bash build.sh

# Install dependencies and run tests
npm install
npm test

# Lint
npm run lint
```

## Architecture

### Core Library Structure

The library is organized around these key components:

1. **SVGDiagram** (`include/svg_diagram.h`) - Main entry point. Creates and manages diagrams containing nodes, edges, and subgraphs.

2. **SVGNode/SVGEdge/SVGGraph** (`include/svg_nodes.h`) - Graph elements:
   - `SVGNode`: Shapes (circle, ellipse, rect, record, doublecircle, none)
   - `SVGEdge`: Connections with arrows (line or spline interpolation)
   - `SVGGraph`: Subgraph/cluster containers
   - `SVGItem`: Base class for shared attribute handling

3. **SVGDraw classes** (`include/svg_draw.h`) - Low-level SVG primitives (circle, rect, line, path, text, etc.) that get converted to XML elements.

4. **XMLElement** (`include/xml_element.h`) - XML generation layer for producing SVG output.

5. **Text sizing** (`include/svg_text_size.h`) - Text dimension estimation. Uses approximations by default; PangoCairo available for accuracy.

### Source Organization

- `include/` - Public headers
- `src/diagram/` - Node, edge, graph implementations
- `src/svg/` - SVGDraw shape implementations
- `python/bindings.cpp` - pybind11 bindings
- `wasm/svg_diagram_wasm.cpp` - Emscripten bindings
- `tests/` - GoogleTest test files organized by component

### Rendering Flow

1. User creates `SVGDiagram`, adds nodes/edges with positions
2. `diagram.render()` is called
3. Graph elements produce `SVGDraw` objects via `produceSVGDraws()`
4. `SVGDraw` objects generate `XMLElement` trees
5. XML is serialized to SVG string

### Node Shapes

Defined as constants on `SVGNode`:
- `SHAPE_CIRCLE`, `SHAPE_DOUBLE_CIRCLE`, `SHAPE_ELLIPSE`
- `SHAPE_RECT`, `SHAPE_RECORD`, `SHAPE_NONE`

### Edge Types

- `SPLINES_LINE` - Straight line connections
- `SPLINES_SPLINE` - Bezier curve connections
- Arrow heads: `ARROW_NORMAL`, `ARROW_EMPTY`, `ARROW_NONE`

## Testing

C++ tests are in `tests/` with subdirectories:
- `svg_draw/` - Low-level drawing tests
- `svg_node/` - Node shape tests
- `svg_edge/` - Edge and arrow tests
- `example/` - Integration tests that render complete diagrams
- `docs/` - Tests matching documentation examples

Python tests are in `python/tests/docs/` mirroring the documentation.

## Dependencies

- PangoCairo (optional): `brew install cairo pango pkg-config` (macOS) or `apt install libcairo2-dev libpango1.0-dev pkg-config` (Linux)
- Emscripten SDK required for WASM build
