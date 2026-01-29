import LASMnemonicsID.utils.mnemonics as mnm
from LASMnemonicsID.utils.mnemonics import (
    gamma_names,
    sp_names,
    caliper_names,
    deepres_names,
    rxo_names,
    density_names,
    density_correction_names,
    neutron_names,
    dtc_names,
    dts_names,
    pe_names,
)
import os
import pathlib
import pandas as pd
import lasio
from os.path import join
from sys import stdout
from pathlib import Path





# Function that create the mnemonic dictionary
def create_mnemonic_dict(
    gamma_names,
    sp_names,
    caliper_names,
    deepres_names,
    rxo_names,
    density_names,
    density_correction_names,
    neutron_names,
    dtc_names,
    dts_names,
    pe_names,
):
    """
    Function that create the mnemonic dictionary with the mnemonics per log type in the utils module
    """

    mnemonic_dict = {
        "gamma": gamma_names,
        "sp": sp_names,
        "caliper": caliper_names,
        "deepres": deepres_names,
        "rxo": rxo_names,
        "density": density_names,
        "density_correction": density_correction_names,
        "neutron": neutron_names,
        "dtc": dtc_names,
        "dts": dts_names,
        "pe": pe_names,
    }
    return mnemonic_dict



def parseLAS(directory_path, verbose=True):
    """
    Parse all LAS files in directory (recursive) into dict of DataFrames or single DataFrame.
    
    Args:
        directory_path (str/Path): Directory containing LAS files
        verbose (bool): Print processing info
        
    Returns:
        dict or DataFrame: {folder: {well: df}} or single df if one file found
    """
    directory_path = Path(directory_path)
    well_logs = {}
    
    # Find all LAS files recursively
    las_files = list(directory_path.rglob("*.las"))
    
    if not las_files:
        if verbose:
            print("No LAS files found.")
        return {}
    
    if len(las_files) == 1:
        # Return single DataFrame if only one file
        return _read_single_las(las_files[0], verbose)
    
    # Multiple files: group by parent folder
    for las_file in las_files:
        folder_name = las_file.parent.name
        if folder_name not in well_logs:
            well_logs[folder_name] = {}
        
        df = _read_single_las(las_file, verbose)
        if df is not None:
            well_name = _get_well_name(las_file)
            well_logs[folder_name][well_name] = df
    
    return well_logs


def _read_single_las(las_file_path, verbose):
    """Read single LAS file to DataFrame"""
    try:
        las_data = lasio.read(las_file_path)
        df = las_data.df()
        if df is None or df.empty:
            if verbose:
                print(f"✗ Empty DataFrame: {las_file_path.name}")
            return None
            
        df.index = df.index.astype(float)
#        df.dropna(inplace=True)
        
        # Standardize GR curve
        _standardize_gr_curve(las_data, df)
        
        if verbose:
            print(f"✓ {las_file_path.name}")
        return df
        
    except lasio.exceptions.LASHeaderError as e:
        if verbose:
            print(f"✗ LASHeaderError in {las_file_path.name}: {e}")
    except Exception as e:
        if verbose:
            print(f"✗ Error in {las_file_path.name}: {type(e).__name__}: {e}")
    return None


def _get_well_name(las_file_path):
    """Extract well name from LAS file"""
    try:
        las_data = lasio.read(las_file_path)
        return str(las_data.well.WELL.value).strip()
    except:
        return las_file_path.stem


def _standardize_gr_curve(las_data, df):
    """Rename gamma ray curve to GR"""
    global gamma_names  # Assuming gamma_names defined elsewhere
    for curve in las_data.curves:
        if curve.mnemonic.lower() in gamma_names:
            df.rename(columns={curve.mnemonic: "GR"}, inplace=True)
            break


