import pytest
from LASMnemonicsID.utils.mnemonics import (
    find_column, mnemonic_dict, gamma_names, sp_names, 
    create_mnemonic_dict
)

def test_create_mnemonic_dict():
    result = create_mnemonic_dict(gamma_names, sp_names, [], [], [], [], [], [], [], [], [])
    assert isinstance(result, dict)
    assert "gamma" in result
    assert len(result["gamma"]) == len(gamma_names)

def test_find_column_gamma(single_las_path):
    import lasio
    las = lasio.read(single_las_path)
    df = las.df()
    col = find_column(df, "gamma")
    assert col is not None  # GR should exist after standardization
    assert col.upper() in [name.upper() for name in gamma_names]

def test_find_column_sp(single_las_path):
    import lasio
    las = lasio.read(single_las_path)
    df = las.df()
    col = find_column(df, "sp")
    # SP may not exist, but function should return None gracefully
    assert col is None or col.upper() in [name.upper() for name in sp_names]

@pytest.mark.parametrize("curve_type", ["gamma", "density", "neutron", "dtc"])
def test_find_column_exists(single_las_path, curve_type):
    import lasio
    las = lasio.read(single_las_path)
    df = las.df()
    if not df.empty:
        col = find_column(df, curve_type)
        if col:
            assert col in df.columns
