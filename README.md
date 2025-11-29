# hloc-cli
CLI for [HLoc](https://github.com/cvg/Hierarchical-Localization). Allows to run a [`COLMAP` like SfM pipeline](https://colmap.github.io/tutorial.html#structure-from-motion) using Deep Learning models for feature extraction and matching.

## Installation

```bash
# Clone and install HLoc (local clone install is necessary)
git clone --recursive https://github.com/cvg/Hierarchical-Localization
cd Hierarchical-Localization/
pip install -e .
# Install the CLI
pip install git+https://github.com/hummat/hloc-cli.git
```

## Usage

```bash
hloc --help
```
