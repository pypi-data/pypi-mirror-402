# Mus Musculus Tracker 🐁

[![PyPI version](https://img.shields.io/pypi/v/mus-musculus-tracker.svg)](https://pypi.org/project/mus-musculus-tracker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A professional **YOLO-based** tool designed for automated detection, Region of Interest (ROI) cropping, and movement tracking of mice (*Mus musculus*) in a circular arena.

## 📋 Features

- **Automated Detection:** Powered by YOLO (v.12) for robust animal identification.
- **Smart ROI Cropping:** Automatically crops video borders to focus on the arena/cage.
- **Trajectory Tracking:** Extracts movement data and tracking coordinates.
- **CLI Ready:** Easy-to-use Command Line Interface for batch processing.

## 🚀 Installation

### Via Pip (Recommended)
You can install the tracker directly from PyPI:

```bash
pip install mus-musculus-tracker
```

### Via Conda (For Development)
To set up a development environment, use the provided environment.yml:

```bash
gh repo clone juancolonna/mouse-tracker
cd mouse-tracker
conda env create -f environment.yml
conda activate mouse-tracker
pip install mus-musculus-tracker
```

## 🛠 Usage
Once installed, the mouse-track command will be available in your terminal. To start tracking on a video file, simply run:

```bash
mouse-track path/to/your/video.mp4
```

## 📑 Requirements
Python: >= 3.13

Main Dependencies:

ultralytics (YOLO)

opencv-python

moviepy

tqdm

## ✍️ Authors
Juan G. Colonna <juancolonna@icomp.ufam.edu.br>

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.