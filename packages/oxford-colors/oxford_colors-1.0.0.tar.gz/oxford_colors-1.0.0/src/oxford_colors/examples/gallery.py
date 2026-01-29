"""
Gallery of example plots using Oxford Colors.
This script generates various types of plots to demonstrate the Oxford Colors library.
"""
import numpy as np
import matplotlib.pyplot as plt
from oxford_colors import oxford_style, OXFORD_COLORS

# Sample data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
y3 = np.sin(x) * np.cos(x)
categories = ['A', 'B', 'C', 'D', 'E']
values = [23, 45, 56, 78, 32]
scatter_x = np.random.randn(50)
scatter_y = np.random.randn(50)
hist_data = np.random.normal(0, 1, 1000)

def create_line_plot():
    """Create a line plot with Oxford colors."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y1, label='sin(x)', linewidth=2)
        ax.plot(x, y2, label='cos(x)', linewidth=2)
        ax.plot(x, y3, label='sin(x)cos(x)', linewidth=2)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_title('Line Plot with Oxford Colors')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('line_plot.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_line_plot_with_markers():
    """Create a line plot with markers."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x[::5], y1[::5], 'o-', label='sin(x)', markersize=6, linewidth=2)
        ax.plot(x[::5], y2[::5], 's-', label='cos(x)', markersize=6, linewidth=2)
        ax.plot(x[::5], y3[::5], '^-', label='sin(x)cos(x)', markersize=6, linewidth=2)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_title('Line Plot with Markers')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('line_plot_markers.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_scatter_plot():
    """Create a scatter plot."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(scatter_x, scatter_y, alpha=0.7, s=60)
        ax.set_xlabel('X values')
        ax.set_ylabel('Y values')
        ax.set_title('Scatter Plot')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('scatter_plot.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_scatter_plot_colored():
    """Create a scatter plot with colored points."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = np.random.rand(len(scatter_x))
        scatter = ax.scatter(scatter_x, scatter_y, c=colors, alpha=0.7, s=60, cmap='viridis')
        ax.set_xlabel('X values')
        ax.set_ylabel('Y values')
        ax.set_title('Colored Scatter Plot')
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, label='Color Scale')
        plt.tight_layout()
        plt.savefig('scatter_plot_colored.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_bar_chart():
    """Create a bar chart."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(categories, values)
        ax.set_xlabel('Categories')
        ax.set_ylabel('Values')
        ax.set_title('Bar Chart')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{value}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('bar_chart.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_horizontal_bar_chart():
    """Create a horizontal bar chart."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(categories, values)
        ax.set_xlabel('Values')
        ax.set_ylabel('Categories')
        ax.set_title('Horizontal Bar Chart')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
                   f'{value}', ha='left', va='center')
        
        plt.tight_layout()
        plt.savefig('horizontal_bar_chart.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_histogram():
    """Create a histogram."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(hist_data, bins=30, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.set_title('Histogram')
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig('histogram.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_multiple_histograms():
    """Create multiple histograms."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        data1 = np.random.normal(0, 1, 1000)
        data2 = np.random.normal(2, 1.5, 1000)
        ax.hist(data1, bins=30, alpha=0.7, label='Dataset 1')
        ax.hist(data2, bins=30, alpha=0.7, label='Dataset 2')
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.set_title('Multiple Histograms')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig('multiple_histograms.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_subplots():
    """Create multiple subplots."""
    with oxford_style():
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Line plot
        ax1.plot(x, y1, linewidth=2)
        ax1.set_title('Line Plot')
        ax1.grid(True, alpha=0.3)
        
        # Scatter plot
        ax2.scatter(scatter_x, scatter_y, alpha=0.7, s=60)
        ax2.set_title('Scatter Plot')
        ax2.grid(True, alpha=0.3)
        
        # Bar chart
        ax3.bar(categories, values)
        ax3.set_title('Bar Chart')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Histogram
        ax4.hist(hist_data, bins=20, alpha=0.7)
        ax4.set_title('Histogram')
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('subplots.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_custom_colors():
    """Create plots with custom Oxford colors."""
    custom_colors = ["oxford_blue", "oxford_pink", "oxford_green", "oxford_orange"]
    with oxford_style(colors=custom_colors):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y1, label='sin(x)', linewidth=2)
        ax.plot(x, y2, label='cos(x)', linewidth=2)
        ax.plot(x, y3, label='sin(x)cos(x)', linewidth=2)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_title('Custom Oxford Colors')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('custom_colors.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_stacked_bar():
    """Create a stacked bar chart."""
    with oxford_style():
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sample data for stacked bars
        categories = ['Q1', 'Q2', 'Q3', 'Q4']
        values1 = [20, 35, 30, 35]
        values2 = [25, 25, 15, 20]
        values3 = [15, 20, 25, 15]
        
        width = 0.6
        ax.bar(categories, values1, width, label='Product A')
        ax.bar(categories, values2, width, bottom=values1, label='Product B')
        ax.bar(categories, values3, width, bottom=np.array(values1) + np.array(values2), label='Product C')
        
        ax.set_xlabel('Quarter')
        ax.set_ylabel('Sales')
        ax.set_title('Stacked Bar Chart')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig('stacked_bar.png', dpi=300, bbox_inches='tight')
        plt.close()

if __name__ == "__main__":
    print("Generating Oxford Colors gallery...")
    
    # Create all example plots
    create_line_plot()
    print("✓ Line plot created")
    
    create_line_plot_with_markers()
    print("✓ Line plot with markers created")
    
    create_scatter_plot()
    print("✓ Scatter plot created")
    
    create_scatter_plot_colored()
    print("✓ Colored scatter plot created")
    
    create_bar_chart()
    print("✓ Bar chart created")
    
    create_horizontal_bar_chart()
    print("✓ Horizontal bar chart created")
    
    create_histogram()
    print("✓ Histogram created")
    
    create_multiple_histograms()
    print("✓ Multiple histograms created")
    
    create_subplots()
    print("✓ Subplots created")
    
    create_custom_colors()
    print("✓ Custom colors plot created")
    
    create_stacked_bar()
    print("✓ Stacked bar chart created")
    
    print("\nGallery complete! All plots saved as PNG files.")
