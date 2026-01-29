# -*- coding: utf-8 -*-
"""
zh-CN National Map
===================================

Import ``easyclimate-map`` for loading China boundary data, matplotlib.pyplot for plotting, and cartopy.crs for map projections.
These libraries together support the retrieval and visualization of geographic data.
"""
import easyclimate_map as eclmap
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# %%
# Line
# -----------------
# Use ``easyclimate_map.get_zh_CN_nation(type="line")`` to retrieve the line-type GeoDataFrame of China's national boundaries.
# This data includes boundary line segments and can be used to draw outlines.
# Output: Print the GeoDataFrame to verify data loading.
zh_border_line = eclmap.get_zh_CN_nation(type = "line")
zh_border_line

# %%
# Use GeoPandas' plot() method for quick visualization of the boundary line.
# This step is for initial data inspection without custom projections.
zh_border_line.plot()

# %%
# Create a subplot with PlateCarree projection (central longitude 180°), set geographic extent [70-140°E, 0-50°N].
# Add gridlines, coastlines, and China's boundary line geometries (red lines, no fill).
# This step demonstrates advanced map projections and geometry overlays.
# Parameter Details:
# 
# - set_extent: Defines the map display range.
# - gridlines: Adds latitude/longitude grid with labels.
# - coastlines: Draws global coastlines (50m resolution).
# - add_geometries: Overlays boundary geometries with red edges, line width 0.3.
fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)})

ax.set_extent([70, 140, 0, 50])
ax.gridlines(
    draw_labels=["left", "bottom"], 
    color="grey", 
    alpha=0.5, linestyle="--"
)
ax.coastlines(color="k", lw = 0.5, resolution = "50m")
ax.add_geometries(
    zh_border_line.geometry,
    crs = ccrs.PlateCarree(),
    facecolor = "none",
    edgecolor = "r",
    lw = 0.3
)

# %%
# Polygon
# -----------------
# Use ``easyclimate_map.get_zh_CN_nation(type="polygon")`` to retrieve the polygon-type GeoDataFrame of China's national boundaries.
# This data includes closed polygon areas for boundaries and can be used for area filling.
zh_border_polygon = eclmap.get_zh_CN_nation(type = "polygon")
zh_border_polygon

# %%
# Use GeoPandas' plot() method for quick visualization of the boundary polygon.
# This step is for initial data inspection without custom projections.
# Output: Display the default Matplotlib plot of the filled boundary.
zh_border_polygon.plot()

# %%
# Create a subplot with PlateCarree projection (central longitude 180°), set geographic extent [70-140°E, 0-50°N].
# Add gridlines, coastlines, and China's boundary polygon geometries (light blue fill, no edges).
# This step demonstrates area fill effects, suitable for region highlighting or climate zoning maps.
# Parameter Details:
# 
# - Similar to above step, but with facecolor="lightblue" for area fill and edgecolor="none" for no borders.
# - Applicable for overlaying other data layers, such as temperature fields or precipitation distributions.
fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)})

ax.set_extent([70, 140, 0, 50])
ax.gridlines(
    draw_labels=["left", "bottom"], 
    color="grey", 
    alpha=0.5, linestyle="--"
)
ax.coastlines(color="k", lw = 0.5, resolution = "50m")
ax.add_geometries(
    zh_border_polygon.geometry,
    crs = ccrs.PlateCarree(),
    facecolor = "lightblue",
    edgecolor = "none",
    lw = 0.3
)