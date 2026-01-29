# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GraphLayout is a multi-platform library for visualizing directed graphs using hierarchical (Sugiyama-style) layout algorithms. It provides:
- C++ core library
- Python bindings (PyPI: `sp-graph-layout`)
- JavaScript/WebAssembly (npm: `sp-graph-layout`)

## Build Commands

### C++ (CMake)

```bash
# Configure and build
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGRAPH_LAYOUT_ENABLE_TESTS=ON
cmake --build build --config Release

# Run tests
cd build && ctest -C Release --output-on-failure

# Build with coverage
cmake -B build -DGRAPH_LAYOUT_ENABLE_TESTS=ON -DGRAPH_LAYOUT_ENABLE_COVERAGE=ON
```

**CMake options:**
- `GRAPH_LAYOUT_ENABLE_TESTS` - Enable C++ unit tests
- `GRAPH_LAYOUT_ENABLE_RANDOM_TESTS` - Enable random test suite
- `GRAPH_LAYOUT_ENABLE_STRICT` - Enable strict compiler warnings (-Wall -Wextra -Werror)
- `GRAPH_LAYOUT_ENABLE_COVERAGE` - Enable coverage reporting
- `GRAPH_LAYOUT_BIND_PYTHON` - Build Python bindings
- `GRAPH_LAYOUT_BIND_ES` - Build WASM/ECMAScript bindings

### Python

```bash
# Install in dev mode with test dependencies
pip install scikit-build-core pybind11
pip install -e ".[test]"

# Run tests
pytest -v python/tests

# Lint and format check
black --check python/wrapper python/tests
isort --check-only python/wrapper python/tests
flake8 --max-line-length=120 python/wrapper python/tests
```

### JavaScript/WASM

```bash
cd wasm

# Build (requires Emscripten SDK)
npm run build

# Lint
npm run lint

# Test
npm test
```

## Architecture

The library implements the Sugiyama hierarchical graph layout algorithm as a configurable 4-stage pipeline:

1. **Feedback Arc Set** (`include/directed/feedback_arcs.h`) - Find and reverse edges creating cycles
   - Methods: `EADES_93`, `MIN_ID`

2. **Layer Assignment** (`include/directed/layer_assignment.h`) - Assign vertices to horizontal layers
   - Methods: `TOPOLOGICAL`, `MIN_NUM_OF_LAYERS`, `GANSNER_93`, `MIN_TOTAL_EDGE_LENGTH`

3. **Cross Minimization** (`include/directed/cross_minimization.h`) - Minimize edge crossings between layers
   - Methods: `BARYCENTER`, `MEDIAN`, `PAIRWISE_SWITCH`

4. **Vertex Positioning** (`include/directed/vertex_positioning.h`) - Compute final coordinates
   - Methods: `BRANDES_KOPF`

### Key Classes

- `DirectedGraphHierarchicalLayout` (`include/graph_layout.h`) - Main entry point, orchestrates the pipeline
- `SPDirectedGraph` (`include/common/graph_def.h`) - Core graph data structure
- `Attributes` (`include/common/graph_attributes.h`) - Graph/vertex/edge styling and configuration

### Source Layout

- `include/` - Public headers (common/ for shared, directed/ for layout algorithms)
- `src/` - C++ implementations mirroring include/ structure
- `tests/` - C++ unit tests (Google Test) organized by algorithm stage
- `python/` - Python bindings (pybind11) and wrapper package
- `wasm/` - JavaScript/WASM bindings (Emscripten)
- `docs/` - Sphinx documentation

### External Dependencies

- **SVGDiagram** (v1.7.0) - SVG rendering, fetched via CMake FetchContent
- **pybind11** (v3.0) - Python bindings
- **Google Test** (v1.17.0) - C++ unit tests
- **PangoCairo** (optional) - Accurate text measurements on macOS/Linux

## Implementation Notes

### Brandes-Köpf Algorithm (Vertex Positioning)

The `VertexPositioning` class (`src/directed/vertex_positioning.cpp`) implements the Brandes-Köpf algorithm in two phases:

1. **verticalAlignment** - Creates vertical alignment blocks by finding median neighbors across layers. Returns `roots` (block root for each vertex) and `aligns` (circular linked list within blocks).

2. **horizontalCompaction** - Assigns X coordinates to blocks using a sink-based approach. The `sinks` array tracks which "sink tree" each block belongs to for coordinating shifts between independent block groups.

The algorithm runs 4 times with different `forward`/`leftToRight` combinations, then takes the median position for each vertex.

### Known Edge Cases

1. **sortIncidentEdges** (`vertex_positioning.cpp:48-56`) - Accesses `layering.positions[i-1]` and `layering.positions[i+1]` without bounds checking. Safe only because layer 0 vertices have no in-edges and last layer vertices have no out-edges in a proper hierarchical layout.

2. **Barycenter division** (`cross_minimization.cpp:276,281`) - Divides by in/out degree without zero-check. Safe because the algorithm skips boundary layers where degree could be zero.

3. **Gansner93 edge replacement** (`layer_assignment.cpp:131`) - Calls `graph.getEdge(minSlackId)` without checking if `minSlackId == -1` (no replacement edge found).

### Testing

Tests are organized by algorithm stage in `tests/`. To run a specific test:
```bash
./build/runTests --gtest_filter="TestName*"
```

Enable random tests with `-DGRAPH_LAYOUT_ENABLE_RANDOM_TESTS=ON` for broader coverage.
