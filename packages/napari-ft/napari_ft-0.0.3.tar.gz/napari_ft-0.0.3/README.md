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
- Interactively draw rectangular boxes on the Fourier transform by clicking and dragging
- Apply inverse Fourier transform with frequency masking (keeping only frequencies inside the boxes)
- See real-time updates of the filtered image as you draw new boxes
- Reset all boxes with a single button click

The filtered image automatically updates while you're drawing boxes, providing immediate visual feedback of your frequency selection.

### How to Use

1. Load a 2D image into napari viewer
2. Open the widget: `Plugins -> napari-ft -> Fourier Transform Filter`
3. Select your image from the dropdown menu
4. The FFT-shifted Fourier transform appears in the widget
5. Click and drag on the Fourier transform to draw boxes around frequencies you want to keep
6. Click "Apply Filter" to create the filtered image (appears in viewer)
7. Draw additional boxes - the filtered image updates automatically in real-time
8. Click "Reset Boxes" to clear all boxes and start over

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
