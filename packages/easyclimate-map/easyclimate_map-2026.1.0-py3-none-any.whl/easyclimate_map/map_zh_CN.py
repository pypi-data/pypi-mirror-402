"""
zh_CN Map
"""

import geopandas as gpd
from typing import Literal
from pathlib import Path
from geopandas import GeoDataFrame
from .tool import read_shapefile_from_7z

__all__ = [
    "get_zh_CN_nation",
    "get_zh_CN_provinces", 
    "get_zh_CN_river1",
    "get_zh_CN_river3",
    "get_zh_CN_1st_administration",
    "get_zh_CN_2nd_administration"
]

script_path = Path(__file__).resolve()
script_folder_path = script_path.parent

def get_zh_CN_nation(
    type: Literal["line", "polygon"] = "line",
) -> GeoDataFrame:
    """
    Get China national boundary data in either line or polygon format.
    
    This function returns geographic boundary data for China's national borders.
    The data includes mainland China's coastline and land borders with neighboring countries.
    
    Parameters
    ----------
    type : {"line", "polygon"}, default "line"
        Geometry type to return:
        - "line": Boundary lines (coastlines and land borders)
        - "polygon": Polygonal representation of China's territory
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing China's national boundary features.
        The CRS is typically EPSG:4326 (WGS84).
    
    Notes
    -----
    - Data source: Standard Chinese cartographic data
    - Encoding: GB2312 (Chinese character encoding)
    - Includes territories claimed by China (e.g., Taiwan, South China Sea islands)

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/zh_CN/plot_zh_CN_nation.py
    """
    if type == "line":
        path = script_folder_path / "shpdata"/ "zh_CN" / "nation" / "bou1_4l.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    elif type == "polygon":
        path = script_folder_path / "shpdata"/ "zh_CN" / "nation" / "bou1_4p.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    else:
        raise ValueError("type must be either 'line' or 'polygon'")
    

def get_zh_CN_provinces(
    type: Literal["line", "polygon"] = "line",
) -> GeoDataFrame:
    """
    Get China provincial-level administrative boundary data.
    
    Returns boundary data for all provincial-level divisions in China, including:
    - 23 provinces
    - 5 autonomous regions
    - 4 municipalities
    - 2 special administrative regions (Hong Kong, Macau)
    
    Parameters
    ----------
    type : {"line", "polygon"}, default "line"
        Geometry type to return:
        - "line": Provincial boundary lines
        - "polygon": Polygonal representation of provincial territories
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with provincial boundary features, including attributes
        for province names and administrative codes.
    
    Notes
    -----
    - Data follows Chinese administrative divisions as of the data source date
    - Taiwan is included as a province of China according to the data source
    - South China Sea islands are typically included in Hainan province

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/zh_CN/plot_zh_CN_provinces.py
    """
    if type == "line":
        path = script_folder_path / "shpdata"/ "zh_CN" / "provinces" / "bou2_4l.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    elif type == "polygon":
        path = script_folder_path / "shpdata"/ "zh_CN" / "provinces" / "bou2_4p.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    else:
        raise ValueError("type must be either 'line' or 'polygon'")
    

def get_zh_CN_river1(
    type: Literal["line", "polygon"] = "line",
) -> GeoDataFrame:
    """
    Get major river systems in China (Level 1 rivers).
    
    Returns geographic data for China's primary river systems, including:
    - Major rivers (Yangtze, Yellow River, Pearl River, etc.)
    - Large lakes and reservoirs
    - Important water bodies
    
    Parameters
    ----------
    type : {"line", "polygon"}, default "line"
        Geometry type to return:
        - "line": River centerlines and watercourse boundaries
        - "polygon": Water body areas (lakes, reservoirs, wide rivers)
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing major river and water body features.
        May include attributes for river names and hydrological classifications.

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/zh_CN/plot_zh_CN_river1.py
    """
    if type == "line":
        path = script_folder_path / "shpdata"/ "zh_CN" / "river1" / "hyd1_4l.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    elif type == "polygon":
        path = script_folder_path / "shpdata"/ "zh_CN" / "river1" / "hyd1_4p.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    else:
        raise ValueError("type must be either 'line' or 'polygon'")
    

def get_zh_CN_river3(
    type: Literal["line", "polygon"] = "line",
) -> GeoDataFrame:
    """
    Get tertiary river systems in China (Level 3 rivers).
    
    Returns geographic data for smaller rivers and streams, including:
    - Tributaries and smaller watercourses
    - Minor lakes and ponds
    - Drainage networks
    
    Parameters
    ----------
    type : {"line", "polygon"}, default "line"
        Geometry type to return:
        - "line": Stream centerlines and minor watercourses
        - "polygon": Small water body areas
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing tertiary river and water body features.
        Provides more detailed hydrological data than Level 1 rivers.
    
    Notes
    -----
    - This dataset offers higher spatial resolution than Level 1 rivers
    - May not include complete coverage for all regions

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/zh_CN/plot_zh_CN_river3.py
    """
    if type == "line":
        path = script_folder_path / "shpdata"/ "zh_CN" / "river3" / "hyd2_4l.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    elif type == "polygon":
        path = script_folder_path / "shpdata"/ "zh_CN" / "river3" / "hyd2_4p.7z"
        return read_shapefile_from_7z(path, encoding="gb2312")
    else:
        raise ValueError("type must be either 'line' or 'polygon'")
    

def get_zh_CN_1st_administration() -> GeoDataFrame:
    """
    Get first-level administrative center locations in China.
    
    Returns point locations for administrative centers at the provincial level,
    including:
    - Provincial capitals
    - Municipal government seats
    - Autonomous region capitals
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with point features representing administrative centers.
        Includes attributes for center names, administrative levels, and codes.
    
    Notes
    -----
    - Typically includes 34 administrative centers (31 provincial-level + 3 special)
    - Coordinates represent government seat locations
    """
    path = script_folder_path / "shpdata"/ "zh_CN" / "administration_1st" / "res1_4m.7z"
    return read_shapefile_from_7z(path, encoding="gb2312")


def get_zh_CN_2nd_administration() -> GeoDataFrame:
    """
    Get second-level administrative center locations in China.
    
    Returns point locations for administrative centers at the prefecture level,
    including:
    - Prefecture-level city governments
    - Autonomous prefecture capitals
    - League administrative centers
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with point features representing prefecture-level
        administrative centers. Includes detailed location attributes.
    
    Notes
    -----
    - Covers approximately 333 prefecture-level divisions in China
    - Includes both urban and rural administrative centers
    """
    path = script_folder_path / "shpdata"/ "zh_CN" / "administration_2nd" / "res2_4m.7z"
    return read_shapefile_from_7z(path, encoding="gb2312")