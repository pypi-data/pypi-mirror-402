# Soil Texture Plot

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://soiltextureplot.streamlit.app/)

This repository contains codebase for soil texture classification and visualization using ternary diagrams. It provides tools to plot soil texture data on texture triangles and classify soil samples according to different classification systems.

## Features

- **Ternary Plotting**: Visualize soil texture data on interactive ternary diagrams
- **Multiple Classification Systems**: Support for USDA and HYPRES soil texture classification systems
- **Interactive Web App**: Streamlit-based application for easy data upload and visualization
- **Flexible Data Input**: Support for CSV files with customizable column mapping
- **Point Classification**: Automatic classification of soil samples into texture classes
- **Customizable Visualization**: Control point sizes, colors, and labels

## Dependencies

- streamlit
- pandas
- numpy
- matplotlib
- mpltern


## Web Application

The web app allows you to:
- Upload CSV files with soil texture data
- Map columns to sand, silt, and clay percentages
- Visualize data on interactive texture triangles
- Customize plot appearance

## Supported Classification Systems

### USDA (United States Department of Agriculture)
The standard USDA soil texture classification system with 12 texture classes.

### HYPRES (HYdraulic PRoperties of European Soils)
A European framework for classifying soils based on their hydrologic properties.

## Data Format

Your CSV file should contain soil texture data with percentages of sand, silt, and clay. The percentages should sum to 100% for each sample.

Example data format:

```csv
sample_id,sand,silt,clay
S1,65,20,15
S2,70,24,6
S3,75,21,4
```

## Acknowledgments

- Built using [mpltern](https://github.com/yuzie007/mpltern) for ternary plotting
- Inspired by soil science classification standards
- Streamlit for the web interface