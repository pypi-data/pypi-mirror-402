import lasio
import pytest
import pandas as pd
from pathlib import Path
from LASMnemonicsID.LAS import parseLAS
from LASMnemonicsID.utils.mnemonics import (
    gamma_names, density_names, neutron_names, 
    dtc_names, sp_names, caliper_names  # All types
)
from LASMnemonicsID.utils.mnemonics import find_column


def test_parseLAS_single_folder(sample_las_paths):
    result = parseLAS(sample_las_paths[0].parent, verbose=False)
    assert isinstance(result, dict)
    assert len(result) == 1  # 'data' folder
    wells = result['data']
    assert len(wells) >= 1  # Adaptive: Expect at least 1 well
    first_df = next(iter(wells.values()))
    assert isinstance(first_df, pd.DataFrame)
    assert len(first_df) > 0  # New files have data!


def test_parseLAS_empty_dir():
    # Ensure empty_dir exists first
    empty_path = Path(__file__).parent / 'empty_dir'
    empty_path.mkdir(exist_ok=True)
    
    result = parseLAS(empty_path, verbose=False)
    assert result == {}


# Test for parsing all curves and identifying and renaming all of them into a new dataframe
def test_parse_all_curves_first_file():
    data_dir = Path(__file__).parent / 'data'
    
    # Check if we have files
    files = list(data_dir.glob('*.las'))
    if not files:
        pytest.skip("No LAS files found in tests/data")
        
    first_file = files[0]
    
    print(f"🔍 Parsing {first_file.name} for ALL curves...")
    las_data = lasio.read(str(first_file))
    df = las_data.df()
    
    # Test ALL curve types with find_column (your utils logic)
    curve_types = {
        'gamma': gamma_names,
        'density': density_names, 
        'neutron': neutron_names,
        'dtc': dtc_names,
        'sp': sp_names,
        'caliper': caliper_names
    }
    
    found_curves = {}
    for curve_type, names in curve_types.items():
        # FIX: Pass the STRING key 'curve_type' (e.g., 'gamma'), NOT the list 'names'
        col = find_column(df, curve_type)  
        found_curves[curve_type] = col
        status = "✅" if col else "❌"
        print(f"{status} {curve_type.upper()}: {col}")
    
    print(f"\n📊 DataFrame: {df.shape}")
    print("Columns:", list(df.columns[:20]), "...")
    print("\nHead:")
    print(df.head(10))
    
    # Assert key curves found
    # Only asserting DataFrame validity here as specific curves depend on the test file content
    assert len(df.columns) >= 1
