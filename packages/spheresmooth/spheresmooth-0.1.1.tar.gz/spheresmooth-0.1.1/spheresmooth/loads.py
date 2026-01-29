"""
Dataset loading utilities for the spheresmooth package.

This module provides access to two example spherical datasets used in
the original R package *spheresmooth*:

1. **APW (Apparent Polar Wander) dataset**  
   A collection of 31 Triassic/Jurassic paleomagnetic poles assembled from
   Kent and Irving (2010).  


2. **Goni tropical cyclone dataset**  
   A trajectory dataset for Typhoon *Goni* (August 2015), provided by the
   Regional Specialized Meteorological Center (RSMC) Tokyo Typhoon Center.  

Both datasets are returned as pandas DataFrames and are packaged with the
Python version of spheresmooth for demonstration and replication purposes.
    """

import pandas as pd
import importlib.resources as resources

def load_apw():
    """
    Load the APW (Apparent Polar Wander) dataset.

    This dataset is taken from Kent and Irving (2010). 
    It consists of 31 Triassic–Jurassic cratonic paleomagnetic poles:
    17 poles from other major cratons rotated into the North American frame,
    combined with 14 observations directly from North America.

    The time span ranges from 243 to 144 Ma (million years ago),
    covering the late Triassic and Jurassic periods.

    Returns
    -------
    pandas.DataFrame
        A dataframe where:
        - Column 1 contains the time points.
        - Columns 2 and 3 contain the observed spherical coordinates
          (colatitude and longitude).
    """
    path = resources.files("spheresmooth").joinpath("data/apw.csv")
    return pd.read_csv(path)

def load_goni():
    """
    Load the tropical cyclone 'Goni' dataset.

    This dataset was provided by the Regional Specialized Meteorological Center
    (RSMC) Tokyo Typhoon Center. It records the trajectory of Typhoon Goni
    observed during August 2015.

    Returns
    -------
    pandas.DataFrame
        A dataframe where:
        - Column 1 contains the time points.
        - Columns 2 and 3 contain the observed spherical coordinates
          (colatitude and longitude) of the cyclone's center.
    """
    path = resources.files("spheresmooth").joinpath("data/goni.csv")
    return pd.read_csv(path)

def load_world_map():
    """
    Return the path to the Natural Earth world shapefile
    bundled inside the spheresmooth package.
    """
    return resources.files("spheresmooth.data.world") / "ne_110m_admin_0_countries.shp"