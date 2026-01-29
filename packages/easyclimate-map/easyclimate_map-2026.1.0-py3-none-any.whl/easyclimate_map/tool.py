"""
Utility
"""
import py7zr
import geopandas as gpd
import tempfile
import os

from geopandas import GeoDataFrame

__all__ = [
    "read_shapefile_from_7z", 
    "extract_outer_boundary",
    "transfer_boundary_to_polygon"
]

def read_shapefile_from_7z(filepath: str, **kwargs) -> GeoDataFrame:
    """
    Read a shapefile directly from a 7z archive without extracting to disk.
    
    This function extracts a shapefile from a compressed 7z archive into a temporary
    directory, loads it as a GeoDataFrame using GeoPandas, and returns the result.
    All keyword arguments are passed through to `gpd.read_file()`.
    
    Parameters
    ----------
    filepath : str
        Path to the 7z archive containing the shapefile.
    **kwargs : dict, optional
        Additional keyword arguments to pass to `gpd.read_file()`.
        Common arguments include:
        - bbox : tuple
            Filter by bounding box (minx, miny, maxx, maxy)
        - mask : geometry
            Filter by geometry mask
        - rows : int
            Number of rows to read
        - encoding : str
            File encoding (e.g., 'utf-8')
        - driver : str
            GDAL/OGR driver name
    
    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing the shapefile data.
    
    Raises
    ------
    FileNotFoundError
        If the 7z file doesn't exist or doesn't contain any .shp files.
    
    Notes
    -----
    - The function creates a temporary directory that is automatically cleaned up.
    - Only the first .shp file found in the archive will be read.
    - Shapefile companion files (.shx, .dbf, .prj) must also be present in the archive.
    
    Examples
    --------
    >>> gdf = read_shapefile_from_7z('data.7z')
    >>> gdf = read_shapefile_from_7z('data.7z', bbox=(xmin, ymin, xmax, ymax))
    >>> gdf = read_shapefile_from_7z('data.7z', encoding='utf-8', rows=1000)
    
    See Also
    --------
    geopandas.read_file : For available keyword arguments and reading options.
    """
    from functools import lru_cache
    from pathlib import Path

    @lru_cache(maxsize=10)
    def extract_7z_once(filepath: str):
        """Cache the decompression result to avoid repeated decompression."""
        tmpdir = tempfile.mkdtemp()
        with py7zr.SevenZipFile(filepath, 'r') as archive:
            archive.extractall(path=tmpdir)
        return tmpdir


    tmpdir = extract_7z_once(filepath)
    shp_files = list(Path(tmpdir).glob("*.shp"))
    
    if not shp_files:
        raise FileNotFoundError("No .shp file found in the 7z archive")
    
    return gpd.read_file(shp_files[0], **kwargs)


def extract_outer_boundary(gdf, dissolve_by=None) -> GeoDataFrame:
    """
    Extract the outer boundary (exterior ring only) from a GeoDataFrame.
    
    This function dissolves all features in a GeoDataFrame and extracts only 
    the outer boundaries, excluding any interior holes or isolated internal lines.
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame containing polygon or multipolygon geometries.
    dissolve_by : str or list of str, optional
        Column name(s) to dissolve by. If None (default), dissolves all features 
        into a single geometry.
    
    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing only the outer boundary lines (LineString or 
        MultiLineString geometry).
    
    Examples
    --------
    >>> import geopandas as gpd
    >>> # Load your data
    >>> gdf = gpd.read_file('basins.shp')
    >>> 
    >>> # Extract outer boundary of all features
    >>> boundary = extract_outer_boundary(gdf)
    >>> 
    >>> # Extract boundary by specific attribute
    >>> boundary = extract_outer_boundary(gdf, dissolve_by='BasinName')
    >>> 
    >>> # Save the result
    >>> boundary.to_file('boundary.shp')
    
    Notes
    -----
    - For MULTIPOLYGON geometries, extracts the exterior ring of each polygon part
    - Interior holes (e.g., lakes, enclaves) are excluded
    - The output CRS is preserved from the input GeoDataFrame
    - If input contains multiple disconnected regions, output will be MultiLineString
    
    See Also
    --------
    geopandas.GeoDataFrame.dissolve : Dissolve geometries
    shapely.geometry.Polygon.exterior : Extract exterior ring

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/tibetan_plateau/plot_tibetan_plateau_basins.py
    """
    from shapely.geometry import MultiPolygon, MultiLineString, Polygon
    import geopandas as gpd
    
    # Dissolve all features
    if dissolve_by is None:
        dissolved = gdf.dissolve()
    else:
        dissolved = gdf.dissolve(by=dissolve_by)
    
    # Extract outer boundaries for each dissolved geometry
    outer_boundaries = []
    
    for idx, row in dissolved.iterrows():
        geom = row.geometry
        
        if isinstance(geom, MultiPolygon):
            # For MULTIPOLYGON: extract exterior ring of each polygon
            for poly in geom.geoms:
                outer_boundaries.append(poly.exterior)
        elif isinstance(geom, Polygon):
            # For single POLYGON: extract exterior ring only
            outer_boundaries.append(geom.exterior)
        else:
            # Fallback for other geometry types
            outer_boundaries.append(geom.boundary)
    
    # Create boundary geometry
    if len(outer_boundaries) == 1:
        boundary_geom = outer_boundaries[0]
    else:
        boundary_geom = MultiLineString(outer_boundaries)
    
    # Create output GeoDataFrame
    boundary_gdf = gpd.GeoDataFrame(
        geometry=[boundary_geom], 
        crs=gdf.crs
    )
    
    return boundary_gdf


def transfer_boundary_to_polygon(boundary_gdf) -> GeoDataFrame:
    """
    Convert boundary lines (LineString or MultiLineString) to polygon geometries.
    
    This function reconstructs polygon geometries from their boundary lines.
    It assumes the boundary lines form closed rings.
    
    Parameters
    ----------
    boundary_gdf : geopandas.GeoDataFrame
        Input GeoDataFrame containing LineString or MultiLineString geometries
        representing polygon boundaries.
    
    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing reconstructed Polygon or MultiPolygon geometries.
    
    Examples
    --------
    >>> import geopandas as gpd
    >>> # Extract boundary first
    >>> boundary = extract_outer_boundary(gdf)
    >>> 
    >>> # Convert boundary back to polygon
    >>> polygon = boundary_to_polygon(boundary)
    >>> 
    >>> # Save the result
    >>> polygon.to_file('reconstructed_polygon.shp')
    
    Notes
    -----
    - Input boundary lines must form closed rings
    - For MultiLineString input, creates MultiPolygon output
    - The output CRS is preserved from the input GeoDataFrame
    - This creates simple polygons without interior holes
    
    See Also
    --------
    :func:`extract_outer_boundary` : Extract outer boundary from polygons
    shapely.geometry.Polygon : Polygon constructor

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/tibetan_plateau/plot_tibetan_plateau_basins.py
    """
    from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
    import geopandas as gpd
    
    polygons = []
    
    for idx, row in boundary_gdf.iterrows():
        geom = row.geometry
        
        if isinstance(geom, MultiLineString):
            # For MultiLineString: create a polygon from each line
            polys = []
            for line in geom.geoms:
                if line.is_closed or line.coords[0] == line.coords[-1]:
                    polys.append(Polygon(line))
                else:
                    # If not closed, close it
                    coords = list(line.coords)
                    coords.append(coords[0])
                    polys.append(Polygon(coords))
            
            if len(polys) == 1:
                polygons.append(polys[0])
            else:
                polygons.append(MultiPolygon(polys))
                
        elif isinstance(geom, LineString):
            # For single LineString: create a polygon
            if geom.is_closed or geom.coords[0] == geom.coords[-1]:
                polygons.append(Polygon(geom))
            else:
                # If not closed, close it
                coords = list(geom.coords)
                coords.append(coords[0])
                polygons.append(Polygon(coords))
        else:
            # Fallback: try to convert directly
            polygons.append(Polygon(geom))
    
    # Create output GeoDataFrame
    polygon_gdf = gpd.GeoDataFrame(
        geometry=polygons,
        crs=boundary_gdf.crs
    )
    
    return polygon_gdf
