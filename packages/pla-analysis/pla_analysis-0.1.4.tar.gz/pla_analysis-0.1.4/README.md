# PLA Analysis Library

![Version](https://img.shields.io/pypi/v/pla_analysis)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**pla_analysis** is a computer vision library designed for the automation and analysis of mechanical tests. This tool allows for the extraction of precise quantitative data (displacement, elongation) from video recordings or image sequences, eliminating the need for physical contact sensors.

## Installation

You can install the library directly from PyPI:

```bash
pip install pla_analysis
```

## Usage Guide

The library is divided into two specialized modules according to the type of mechanical test. The operation of each is detailed below.

---

### 1. Tensile Module (Optical Extensometry)

This module automates elongation measurement in tensile tests by tracking two physical marks on the specimen.

#### Input Requirements
* **Input:** A folder (directory) containing the image sequence (frames) of the test ordered chronologically.
* **Specimen:** Must have **two horizontal black lines** marked on a clear background.

#### Example Code

```python
import pla_analysis

# Path to the folder containing the images .jpg/.tif/.png
frames_folder = "C:/path/to/my_tensile_frames"

# Run analysis
# l0_mm: Real initial distance between the two lines (Default: 35.0 mm)
# a0_mm2: Cross-sectional area of the specimen (Default: 15.0 mm^2)
pla_analysis.tensile.analyze(frames_folder, l0_mm=35.0, a0_mm2=15.0)
```

#### Interactive Workflow

1.  **ROI (Region of Interest) Selection:**
    Upon running the code, the first frame will open. You must draw a box with the mouse that meets two vital conditions:
    * **Must contain BOTH black lines.**
    * Must have some **vertical clearance** (towards the direction the specimen stretches) to avoid losing the lines during the test.
    * **Efficiency:** Try to adjust the width horizontally to the specimen. Selecting an unnecessarily large region will increase computational cost and could slow down the analysis.

2.  **Live Analysis:**
    The program will process the sequence showing a dashboard with line detection and the elongation graph generating frame by frame.

3.  **Results:**
    Upon completion, the maximum displacement will be shown in the terminal, and a window will open with the detailed final graph of `Elongation (mm) vs Frames`.

---

### 2. Body3D Module (Flexion Tracking)

Designed to track the displacement of a specific point (centroid) in flexion tests or rigid body motion.

#### Experiment Preparation (Important)
To ensure proper computer vision performance, the input video must meet the following criteria:
* **Contrast:** The specimen must be light (white) and the background also white or very light.
* **Marker:** Draw a **single black or dark blue dot** on the area you wish to analyze.
* **Editing:** It is recommended to crop the video beforehand to eliminate dead time at the start or end. The less "filler" the video has, the faster and more accurate the analysis will be.

#### Example Code

```python
import pla_analysis

# Path to the video file (.mp4, .avi, etc.)
video_path = "C:/path/to/flexion_test.mp4"

# save_video=True will generate an .mp4 file with the visual result overlaid
pla_analysis.body3d.analyze(video_path, save_video=True)
```

#### Interactive Workflow

1.  **Scale Calibration:**
    The system needs to transform pixels to millimeters.
    * Click on **two points** on the image whose real distance you know (e.g., the width of the specimen).
    * Enter the real distance in millimeters in the terminal (e.g., `10.5`).

2.  **ROI Selection:**
    Select a box enclosing the area where the black dot will move. Ensure sufficient **clearance** so the dot does not exit the frame during maximum flexion.

3.  **Threshold Adjustment:**
    A window with a slider will appear.
    * Move the bar until **only the black dot** is visible in black and the rest of the image appears totally white.
    * Press `ENTER` to confirm.

4.  **Results and Export:**
    The system will automatically generate in your execution folder:
    * `resultado_analisis.mp4`: Live dashboard video.
    * `reporte_comparativo.png`: Static image comparing the initial state (rest) vs. maximum displacement.

---

## Authors

Project developed by students from Mondragon Unibertsitatea:

* **Haritz Aseguinolaza**
* **Aimar Seco**
* **Aratz Zabala**
* **Aitor Otzerin**

## License

This project is distributed under the MIT license. See the `LICENSE` file for more information.