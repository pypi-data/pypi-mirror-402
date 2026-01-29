# napari-ft

[![License BSD-3](https://img.shields.io/pypi/l/napari-ft.svg?color=green)](https://github.com/jules-vanaret/napari-ft/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-ft.svg?color=green)](https://pypi.org/project/napari-ft)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-ft.svg?color=green)](https://python.org)
[![tests](https://github.com/jules-vanaret/napari-ft/workflows/tests/badge.svg)](https://github.com/jules-vanaret/napari-ft/actions)
[![codecov](https://codecov.io/gh/jules-vanaret/napari-ft/branch/main/graph/badge.svg)](https://codecov.io/gh/jules-vanaret/napari-ft)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-ft)](https://napari-hub.org/plugins/napari-ft)
[![npe2](https://img.shields.io/badge/plugin-npe2-blue?link=https://napari.org/stable/plugins/index.html)](https://napari.org/stable/plugins/index.html)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)

A napari plugin for interactive Fourier transform filtering

----------------------------------

This [napari] plugin was generated with [copier] using the [napari-plugin-template] (None).

## Features

**Interactive Fourier Transform Filter Widget**

This widget allows you to:
- Select a 2D image from the napari viewer
- View its FFT-shifted Fourier transform (log magnitude) in the widget
- Interactively draw rectangular or circular regions on the Fourier transform
  - **Left-click and drag**: Create inclusion regions (frequencies to keep)
  - **Right-click and drag**: Create exclusion regions (frequencies to remove)
  - **Middle-click and drag**: Pan the view
  - **Mouse wheel**: Zoom in/out
- Toggle between rectangle and circle shape modes
- Apply inverse Fourier transform with frequency masking
- See real-time updates of the filtered image as you draw new regions
- Reset boxes or view independently

The filtered image automatically updates as you draw, providing immediate visual feedback. The widget tracks changes to the source image data and scale, keeping everything synchronized.

### How to Use

1. Load a 2D image into napari viewer
2. Open the widget: `Plugins -> napari-ft -> Fourier Transform Filter`
3. Select your image from the dropdown menu
4. The FFT-shifted Fourier transform appears in the widget
5. Draw regions on the Fourier transform:
   - Left-click and drag to select frequencies to keep
   - Right-click and drag to exclude specific frequencies
   - Use "Shape" button to toggle between rectangles and circles
6. The filtered image appears automatically and updates in real-time
7. Use mouse wheel to zoom, middle-click to pan
8. Click "Reset Boxes" to clear all regions or "Reset View" to reset zoom/pan

## Installation

You can install `napari-ft` via [pip]:

```
pip install napari-ft
```

If napari is not already installed, you can install `napari-ft` with napari and Qt via:

```
pip install "napari-ft[all]"
```

## Testing

To test the widget, run the included test script:

```bash
python test_ft_widget.py
```

This will open napari with a test image containing multiple frequency components.



## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-ft" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[copier]: https://copier.readthedocs.io/en/stable/
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[napari-plugin-template]: https://github.com/napari/napari-plugin-template

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
