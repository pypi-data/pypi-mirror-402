"""
Tibetan Plateau (Qinghai-Xizang Plateau)
"""
from pathlib import Path
from geopandas import GeoDataFrame
from .tool import read_shapefile_from_7z
from rich import print

__all__ = [
    "get_Tibetan_Plateau_basins",
]

script_path = Path(__file__).resolve()
script_folder_path = script_path.parent

def get_Tibetan_Plateau_basins() -> GeoDataFrame:
    """
    Get Tibetan Plateau basins data in polygon format.
    
    .. tip::

        - Zhang, G. (2019). Dataset of river basins map over the TP（2016）. National Tibetan Plateau / Third Pole Environment Data Center. https://doi.org/10.11888/BaseGeography.tpe.249465.file. https://cstr.cn/18406.11.BaseGeography.tpe.249465.file.
        - Zhang, G.Q., Yao, T.D., Xie, H.J., Kang, S.C., &Lei, Y.B. (2013). Increased mass over the Tibetan Plateau: From lakes or glaciers? Geophysical Research Letters, 40(10), 2125-2130. https://doi.org/10.1002/grl.50462

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing Tibetan Plateau basins.
        The CRS is typically EPSG:4326 (WGS84).

    .. minigallery::
        :add-heading: Example(s) related to the function

        ./dynamic_docs/tibetan_plateau/plot_tibetan_plateau_basins.py
    """
    print(
        "[bold yellow]<easyclimate-map notice>[/bold yellow]: "
        "Please refer to the data usage instructions before using the data."
        "https://doi.org/10.11888/BaseGeography.tpe.249465.file"
    )

    path = script_folder_path / "shpdata"/ "tibetan_plateau" / "TP_basins.7z"
    return read_shapefile_from_7z(path)
