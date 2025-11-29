# hloc-cli
CLI for [HLoc](https://github.com/cvg/Hierarchical-Localization). Allows to run a [`COLMAP` like SfM pipeline](https://colmap.github.io/tutorial.html#structure-from-motion) using Deep Learning models for feature extraction and matching.

## Installation

**Important:** Hierarchical-Localization cannot be installed directly from git via pip because it has git submodules (like `SuperGluePretrainedNetwork`) that require `--recursive` cloning. Pip does not support recursive submodule installation from git URLs.

```bash
# Install HLoc (local install required)
git clone --recursive https://github.com/cvg/Hierarchical-Localization
cd Hierarchical-Localization/
pip install -e .

# Install CLI
pip install git+https://github.com/hummat/hloc-cli.git
```

## Usage

```bash
hloc --help
```
