# Oxford Colors

A Python library providing Oxford University's official color palette for matplotlib visualizations.

## Installation

```bash
pip install oxford_colors
```

## Quick Start

```python
import matplotlib.pyplot as plt
from oxford_colors import oxford_style

# Use Oxford colors with the context manager
with oxford_style():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.plot([1, 2, 3], [1, 2, 3])
    plt.show()
```

## Features

- **Official Oxford Colors**: Complete palette including primary, secondary, neutral, and metallic colors
- **Context Manager**: Temporary color styling that automatically reverts
- **Custom Color Selection**: Choose specific colors from the palette
- **Multiple Plot Types**: Works with line plots, bar charts, scatter plots, histograms, and more
- **Matplotlib Integration**: Seamless integration with matplotlib's color cycle

## Available Colors

### Primary Colors
- `oxford_blue` - The signature Oxford blue (#002147)

### Secondary Colors
A comprehensive palette including:
- `oxford_mauve`, `oxford_peach`, `oxford_potters_pink`
- `oxford_dusk`, `oxford_lilac`, `oxford_sienna`
- `oxford_ccb_red`, `oxford_plum`, `oxford_coral`
- `oxford_lavender`, `oxford_orange`, `oxford_pink`
- `oxford_green`, `oxford_ocean_grey`, `oxford_yellow_ochre`
- And many more...

### Neutral Colors
- `oxford_charcoal`, `oxford_ash_grey`, `oxford_umber`
- `oxford_stone_grey`, `oxford_shell_grey`, `oxford_off_white`

### Metallic Colors
- `oxford_gold`, `oxford_silver`

## Usage Examples

### Basic Line Plot

```python
import matplotlib.pyplot as plt
from oxford_colors import oxford_style

with oxford_style():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [1, 4, 2, 8], label='Series 1')
    ax.plot([1, 2, 3, 4], [2, 3, 4, 5], label='Series 2')
    ax.legend()
    plt.show()
```

### Custom Color Selection

```python
from oxford_colors import oxford_style

# Use specific Oxford colors
with oxford_style(colors=["oxford_blue", "oxford_pink", "oxford_green"]):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.plot([1, 2, 3], [1, 2, 3])
    ax.plot([1, 2, 3], [4, 5, 6])
    plt.show()
```

### Bar Chart

```python
import matplotlib.pyplot as plt
from oxford_colors import oxford_style

with oxford_style():
    fig, ax = plt.subplots()
    categories = ['A', 'B', 'C', 'D']
    values = [23, 45, 56, 78]
    ax.bar(categories, values)
    plt.show()
```

### Scatter Plot

```python
import numpy as np
import matplotlib.pyplot as plt
from oxford_colors import oxford_style

with oxford_style():
    fig, ax = plt.subplots()
    x = np.random.randn(50)
    y = np.random.randn(50)
    ax.scatter(x, y, alpha=0.7)
    plt.show()
```

### Multiple Subplots

```python
import matplotlib.pyplot as plt
import numpy as np
from oxford_colors import oxford_style

with oxford_style():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
    
    # Line plot
    x = np.linspace(0, 10, 100)
    ax1.plot(x, np.sin(x))
    ax1.set_title('Sine Wave')
    
    # Scatter plot
    ax2.scatter(np.random.randn(50), np.random.randn(50))
    ax2.set_title('Scatter Plot')
    
    # Bar chart
    ax3.bar(['A', 'B', 'C'], [10, 20, 15])
    ax3.set_title('Bar Chart')
    
    # Histogram
    ax4.hist(np.random.normal(0, 1, 1000), bins=30)
    ax4.set_title('Histogram')
    
    plt.tight_layout()
    plt.show()
```

## Advanced Usage

### Accessing Individual Colors

```python
from oxford_colors import hex, rgb, OXFORD_COLORS

# Get hex color
blue_hex = hex("oxford_blue")  # '#002147'

# Get RGB tuple
blue_rgb = rgb("oxford_blue")  # (0, 33, 71)

# Access color object directly
blue_color = OXFORD_COLORS["oxford_blue"]
print(blue_color.name)  # "Oxford blue"
print(blue_color.pantone)  # "Pantone 282"
```

### Creating Custom Palettes

```python
from oxford_colors import mpl_palette

# Create a palette with specific colors
custom_palette = mpl_palette([
    "oxford_blue", 
    "oxford_pink", 
    "oxford_green",
    "oxford_orange"
])

# Use with matplotlib
import matplotlib.pyplot as plt
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=custom_palette)
```

## Development

### Installation for Development

```bash
git clone https://github.com/HakamAtassi/oxford_colors.git
cd oxford_colors
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Building the Package

```bash
python -m build
```

## Gallery

The `examples/gallery.py` script generates a comprehensive gallery of plots using Oxford colors:

```bash
python -m oxford_colors.examples.gallery
```

This will create multiple PNG files demonstrating:
- Line plots (with and without markers)
- Scatter plots (single and colored)
- Bar charts (vertical and horizontal)
- Histograms (single and multiple)
- Subplots
- Stacked bar charts
- Custom color selections

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Color References

The colors in this library are based on Oxford University's official brand guidelines and include:
- Official Pantone references where available
- CMYK values for print applications
- RGB values for digital use
- Hex codes for web applications

## Changelog

### Version 1.0.0
- Initial release
- Complete Oxford color palette
- Context manager for temporary styling
- Comprehensive test suite
- Example gallery
- PyPI distribution ready
