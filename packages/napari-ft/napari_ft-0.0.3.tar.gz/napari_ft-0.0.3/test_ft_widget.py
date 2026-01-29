"""
Test script for the Fourier Transform Widget
"""

import napari
import numpy as np

# Create a simple test image with some patterns
size = 256
x, y = np.meshgrid(np.linspace(-5, 5, size), np.linspace(-5, 5, size))

# Create a pattern with multiple frequencies
image = (
    np.sin(2 * np.pi * x)
    + np.sin(4 * np.pi * y)
    + 0.5 * np.sin(6 * np.pi * (x + y))
)
image = (image - image.min()) / (image.max() - image.min())

# Add some noise
image += 0.1 * np.random.randn(*image.shape)

# Create viewer and add image
viewer = napari.Viewer()
viewer.add_image(image, name="test_pattern")

# The widget can be opened from the Plugins menu -> napari-ft -> Fourier Transform Filter
print("Image added to viewer.")
print("Open the widget from: Plugins -> napari-ft -> Fourier Transform Filter")
print("Then:")
print("  1. Select 'test_pattern' from the dropdown")
print("  2. Draw boxes on the Fourier transform by clicking and dragging")
print("  3. Click 'Apply Filter' to see the filtered result")
print("  4. Draw more boxes to update the filter in real-time")
print("  5. Click 'Reset Boxes' to clear all boxes")

napari.run()
