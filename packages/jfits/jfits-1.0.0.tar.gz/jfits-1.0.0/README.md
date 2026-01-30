# jfits

Interactive visualization for numpy arrays and FITS images in astronomy.

**About the name:** This tool was originally built for my own use and workflows. The j is for Jordan.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

jfits provides interactive visualization tools for astronomical data analysis. View and analyze numpy arrays during your processing workflow without writing to disk. Includes support for FITS files with WCS coordinates, Gaussian centroiding, and 3D IFS cube analysis.

## Features

- Interactive display with adjustable vmin/vmax, colormaps, and scaling
- WCS coordinate support with RA/Dec readout on hover
- Circular and elliptical 2D Gaussian centroiding
- 3D cube viewer for IFS data with slice navigation
- Gaussian-weighted spectrum extraction from cubes
- Multiple colormaps: viridis, cividis, inferno, magma, plasma, gray, gray_r
- Log and linear scaling modes

## Installation

```bash
pip install jfits
```

### Requirements

- Python >= 3.8
- numpy >= 1.20.0
- matplotlib >= 3.3.0
- astropy >= 4.0
- scipy >= 1.7.0

### Interactive Backend

jfits requires matplotlib with an interactive backend. Most installations include this by default.

**Interactive mode:**

For interactive sessions (IPython, terminal, Jupyter with `%matplotlib tk`):

```python
import matplotlib.pyplot as plt
plt.ion()
```

With `plt.ion()` enabled:
- Figures appear immediately without `plt.show()`
- You can continue working while windows are open
- Figures update automatically when modified

**Standalone scripts:**

For standalone Python scripts, `plt.ion()` is not needed. Use the traditional approach:

```python
import jfits
import matplotlib.pyplot as plt

display = jfits.InteractiveDisplay(data)
plt.show()  # Blocks until window closed
```

**Backend errors:**

If you encounter backend errors:

```bash
# Ubuntu/Debian (Tkinter):
sudo apt-get install python3-tk

# Or install Qt backend:
pip install PyQt5
```

## Quick Start

### Interactive Session (IPython, Terminal)

```python
import jfits
import numpy as np
import matplotlib.pyplot as plt

# Enable interactive mode
plt.ion()

# Your data processing
data = np.random.randn(512, 512)
processed = data * some_mask + background

# Visualize - window appears immediately
display = jfits.InteractiveDisplay(processed)
# Continue working while window is open
```

### Standalone Script

```python
import jfits
import numpy as np
import matplotlib.pyplot as plt

# Your data processing
data = np.random.randn(512, 512)
processed = data * some_mask + background

# Visualize
display = jfits.InteractiveDisplay(processed)
plt.show()  # Blocks until window closed
```

### Viewing FITS Files

```python
import jfits
import matplotlib.pyplot as plt

plt.ion()  # For interactive session

# Quick view
display = jfits.quick_view('observation.fits')

# Or load data manually
header, data = jfits.get_fits_array('observation.fits')
display = jfits.InteractiveDisplay(data)
```

### 3D Cube Viewing

```python
import jfits
import matplotlib.pyplot as plt

plt.ion()  # For interactive session

# Automatic wavelength detection from header
display = jfits.quick_view_cube('ifs_cube.fits')

# Or specify wavelengths manually
import numpy as np
wavelengths = np.linspace(4000, 7000, 100)
display = jfits.InteractiveDisplayCube(
    cube_data,
    wavelengths=wavelengths,
    wavelength_unit='Angstrom'
)
```

## Interactive Controls

### 2D Display

**Left Panel:**
- Colormap selection (7 options)
- Log/linear scaling toggle
- Mask color (white/black for NaN pixels)
- Centroid window size (5, 10, 20, 50 pixels)
- Centroid mode (Off, Circular, Elliptical)

**Bottom Panel:**
- vmax/vmin sliders for display range
- Colorbar showing current mapping

**Mouse Interaction:**
- Hover to see coordinates and pixel values
- Click (when centroiding enabled) to fit 2D Gaussians

### 3D Cube Display

All 2D controls plus:
- Slice slider for wavelength/spectral navigation
- Spectrum extraction toggle (extract weighted spectrum at clicked position)

## Usage in Jupyter Notebooks

### Local Jupyter (Recommended)

```python
# At top of notebook:
%matplotlib tk

import jfits
import numpy as np

# Separate interactive window
data = np.random.randn(256, 256)
display = jfits.InteractiveDisplay(data)
```

### JupyterLab with ipympl

For embedded interactive widgets:

```bash
# Install ipympl
pip install ipympl
```

In notebook:

```python
%matplotlib widget

import jfits
import numpy as np

data = np.random.randn(256, 256)
display = jfits.InteractiveDisplay(data)
```

Note: ipympl works in JupyterLab only, not classic Jupyter Notebook.

### Cloud Notebooks (Colab, Binder)

Use static display:

```python
%matplotlib inline
import jfits
import numpy as np

data = np.random.randn(100, 100)
ax = jfits.Display(data, vmin=0, vmax=1)
```

## Examples

### Interactive Processing Workflow

```python
import jfits
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

plt.ion()

# Load data
data = fits.getdata('raw_image.fits')

# Process
background = np.median(data)
data_sub = data - background

# Check result interactively
display = jfits.InteractiveDisplay(data_sub)

# Adjust display parameters with sliders and controls
# Once satisfied, continue processing
```

### Centroiding Example

```python
import jfits
import matplotlib.pyplot as plt

plt.ion()

display = jfits.quick_view('star_field.fits')

# In the display window:
# 1. Select "Circular" or "Elliptical" under centroid
# 2. Adjust centroid window size if needed
# 3. Click on sources to fit Gaussians
# Red contours show fitted model
# Title shows fit parameters (RA/Dec if WCS available)
```

### IFS Cube Analysis

```python
import jfits
import matplotlib.pyplot as plt

plt.ion()

display = jfits.quick_view_cube('muse_cube.fits')

# Workflow:
# 1. Use slice slider to navigate wavelengths
# 2. Enable "show spectrum" (yes)
# 3. Enable centroiding (Circular or Elliptical)
# 4. Click on source
# Separate window opens showing flux vs wavelength
```

### Elliptical Galaxy Fitting

```python
import jfits
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

# Create elliptical galaxy model
data = np.zeros((150, 150))
y, x = np.indices(data.shape)

theta = np.radians(45)
x_rot = np.cos(theta) * (x - 75) - np.sin(theta) * (y - 75)
y_rot = np.sin(theta) * (x - 75) + np.cos(theta) * (y - 75)

data += 1000 * np.exp(-(x_rot**2 / (2*8**2) + y_rot**2 / (2*20**2)))
data += np.random.normal(0, 10, data.shape)

display = jfits.InteractiveDisplay(data)

# Use Elliptical centroiding mode
# Recovers sigma_x ~ 8, sigma_y ~ 20, theta ~ 45 degrees
```

## API Reference

### Main Functions

**`quick_view(filename, **kwargs)`**

Quick interactive display of 2D FITS file.

Returns: `InteractiveDisplay` object

**`quick_view_cube(filename, **kwargs)`**

Quick interactive display of 3D FITS cube. Automatically detects wavelength axis from header.

Returns: `InteractiveDisplayCube` object

**`get_fits_array(filename)`**

Read FITS file data and header.

Returns: `(header, data)` or `([headers], [data])` for multi-extension FITS

**`read_wcs(header)`**

Extract WCS from FITS header.

Returns: `astropy.wcs.WCS` object or None

### Classes

**`InteractiveDisplay(arr, wcs=None, **imshowargs)`**

Interactive 2D image display with full control over parameters and Gaussian centroiding.

**Attributes:**
- `ax` - Main image axes (matplotlib Axes object)
- `fig` - Figure object
- `cax` - Colorbar axes
- `wcs` - WCS object (if provided)
- `arr` - Image data array

**`InteractiveDisplayCube(cube, wavelengths=None, wavelength_unit='slice units', **kwargs)`**

Interactive 3D cube display with slice navigation and spectrum extraction. Inherits all `InteractiveDisplay` features.

**`Display(arr, wcs=None, log=False, **imshowargs)`**

Non-interactive 2D display. Returns matplotlib axes for further customization.

## Advanced Usage

### Direct Axes Access

The display object exposes matplotlib axes for advanced customization:

```python
import jfits
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

# Create display
data = np.random.randn(200, 200)
display = jfits.InteractiveDisplay(data)

# Add custom contours on the same axes
other_data = process_another_array()
display.ax.contour(
    other_data / other_data.max(),
    levels=[0.9, 0.7, 0.5, 0.1],
    colors='m'
)

# Add custom annotations
display.ax.plot([50, 100], [50, 100], 'r--', linewidth=2, label='Custom line')
display.ax.legend()

# Access figure for saving
display.fig.savefig('my_analysis.png', dpi=150)
```

**Available attributes:**
- `display.ax` - Main image axes (for plotting, contours, annotations)
- `display.fig` - Figure object (for saving, adjusting layout)
- `display.cax` - Colorbar axes
- `display.wcs` - WCS object (if provided)
- `display.arr` - Image data array

### Custom Display Settings

```python
import jfits
import matplotlib.pyplot as plt

plt.ion()

header, data = jfits.get_fits_array('image.fits')
wcs = jfits.read_wcs(header)

display = jfits.InteractiveDisplay(
    data, 
    wcs=wcs,
    vmin=100, 
    vmax=5000
)
```
## Troubleshooting

### Backend Errors

**Error:** "UserWarning: Matplotlib is currently using agg"

**Solution:**
```python
import matplotlib
matplotlib.use('TkAgg')  # Before importing pyplot
import matplotlib.pyplot as plt
```

### Tkinter Not Found

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**macOS:**
Tkinter is included with Python from python.org

**Windows:**
Reinstall Python with "tcl/tk and IDLE" option checked

### Jupyter Widgets Unresponsive

In Jupyter notebooks, interactive widgets require either a separate window (`%matplotlib tk`) or ipympl (`%matplotlib widget`). The default inline backend does not support interactive controls.

## Platform Support

jfits works on Windows, macOS, and Linux. Matplotlib handles platform-specific rendering automatically. Users need only ensure an interactive backend is installed (typically Tkinter or Qt).

Interactive mode (`plt.ion()`) is platform-independent and works with all GUI backends.

## Contributing

Contributions are welcome. Please fork the repository, create a feature branch, and submit a pull request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built on matplotlib, numpy, astropy, and scipy.

## Contact

Issues: https://github.com/yourusername/jfits/issues
