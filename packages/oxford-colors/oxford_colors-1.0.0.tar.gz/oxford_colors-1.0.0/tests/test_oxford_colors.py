"""
Test suite for oxford_colors package.
"""
import pytest
import matplotlib.pyplot as plt
import numpy as np
from oxford_colors import oxford_style, mpl_palette, OXFORD_COLORS, DEFAULT_PALETTE

# Sample data for testing
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
data = np.random.normal(0, 1, 1000)


def test_oxford_style_line_plot():
    """Test line plots with oxford_style context manager."""
    with oxford_style():
        fig, ax = plt.subplots()
        line1, = ax.plot(x, y1, label='sin(x)')
        line2, = ax.plot(x, y2, label='cos(x)')
        
        # Check if lines use colors from the default palette
        assert line1.get_color() == DEFAULT_PALETTE[0]
        assert line2.get_color() == DEFAULT_PALETTE[1]
        
        # Test legend
        ax.legend()
        plt.close(fig)


def test_oxford_style_scatter_plot():
    """Test scatter plots with oxford_style context manager."""
    with oxford_style():
        fig, ax = plt.subplots()
        scatter = ax.scatter(x[::10], y1[::10], label='points')
        
        # Check scatter plot color - compare with first color in default palette
        expected_color = plt.matplotlib.colors.to_rgba(DEFAULT_PALETTE[0])
        actual_color = scatter.get_facecolor()[0]  # Get first color
        assert np.allclose(actual_color, expected_color)
        plt.close(fig)


def test_oxford_style_bar_chart():
    """Test bar charts with oxford_style context manager."""
    with oxford_style():
        fig, ax = plt.subplots()
        bars = ax.bar([1, 2, 3], [3, 7, 2])
        
        # Check that bars use colors from the Oxford palette
        # Bar charts may use different colors than the first few in the palette
        # So we just check that the colors are from the Oxford palette
        for i, bar in enumerate(bars):
            bar_color = bar.get_facecolor()
            # Convert to hex for comparison
            bar_hex = plt.matplotlib.colors.to_hex(bar_color)
            # Check if it's in our palette (allowing for slight variations)
            found = False
            for palette_hex in DEFAULT_PALETTE:
                if bar_hex.lower() == palette_hex.lower():
                    found = True
                    break
            assert found, f"Bar color {bar_hex} not found in Oxford palette"
        plt.close(fig)


def test_oxford_style_histogram():
    """Test histograms with oxford_style context manager."""
    with oxford_style():
        fig, ax = plt.subplots()
        n, bins, patches = ax.hist(data, bins=20, alpha=0.7)
        
        # Check histogram patch colors
        expected_color = plt.matplotlib.colors.to_rgba(DEFAULT_PALETTE[0])
        # Account for alpha in the comparison
        expected_color_with_alpha = (*expected_color[:3], 0.7)
        for patch in patches:
            assert np.allclose(patch.get_facecolor(), expected_color_with_alpha)
        plt.close(fig)


def test_custom_color_cycle():
    """Test custom color cycle with oxford_style."""
    custom_colors = ["oxford_blue", "oxford_pink", "oxford_green"]
    with oxford_style(colors=custom_colors):
        fig, ax = plt.subplots()
        lines = [ax.plot(x, y1)[0], ax.plot(x, y2)[0]]
        
        # Convert color names to hex for comparison
        expected_colors = [OXFORD_COLORS[c].hex for c in custom_colors]
        
        # Check line colors match custom colors
        assert lines[0].get_color() == expected_colors[0]
        assert lines[1].get_color() == expected_colors[1]
        plt.close(fig)


def test_rcparams_override():
    """Test that oxford_style properly restores original settings."""
    original_cycler = plt.rcParams['axes.prop_cycle']
    
    with oxford_style():
        # Should use Oxford colors
        fig, ax = plt.subplots()
        line = ax.plot([1, 2, 3], [1, 4, 9])[0]
        assert line.get_color() == DEFAULT_PALETTE[0]
        plt.close(fig)
    
    # Should be back to original settings
    assert plt.rcParams['axes.prop_cycle'] == original_cycler


def test_mpl_palette():
    """Test the mpl_palette function."""
    # Test default palette
    default_palette = mpl_palette()
    assert isinstance(default_palette, list)
    assert len(default_palette) > 0
    assert all(isinstance(c, str) for c in default_palette)
    
    # Test custom palette
    custom_colors = ["oxford_blue", "oxford_pink"]
    palette = mpl_palette(custom_colors)
    assert len(palette) == 2
    assert palette[0] == OXFORD_COLORS["oxford_blue"].hex
    assert palette[1] == OXFORD_COLORS["oxford_pink"].hex


def test_oxford_style_with_subplots():
    """Test oxford_style with multiple subplots."""
    with oxford_style():
        fig, (ax1, ax2) = plt.subplots(1, 2)
        
        # First subplot
        line1 = ax1.plot(x, y1)[0]
        ax1.set_title('Sin(x)')
        
        # Second subplot
        bars = ax2.bar([1, 2, 3], [3, 7, 2])
        ax2.set_title('Bar Chart')
        
        # Check colors are consistent
        assert line1.get_color() == DEFAULT_PALETTE[0]
        assert bars[0].get_facecolor() == plt.matplotlib.colors.to_rgba(DEFAULT_PALETTE[0])
        
        plt.close(fig)


if __name__ == "__main__":
    pytest.main(["-v", "--color=yes"])
