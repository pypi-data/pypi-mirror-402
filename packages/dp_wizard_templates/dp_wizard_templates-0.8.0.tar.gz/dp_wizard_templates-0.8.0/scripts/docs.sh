#!/bin/bash

set -euo pipefail

# Just loading the jupytext module will try to execute pandoc:
# It wants to know the installed version. So, we need PDOC_ALLOW_EXEC.
PDOC_ALLOW_EXEC=1 pdoc -o docs/ dp_wizard_templates
mkdir docs/examples || true
cp examples/*.* docs/examples

echo "Docs available at: docs/index.html"