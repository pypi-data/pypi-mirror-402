
<p align="center">
  <img src="https://raw.githubusercontent.com/Nobleza-Energy/LASMnemonicsID/main/logo.png" alt="LASMnemonicsID Logo" width="200"/>
</p>

<h1 align="center">LASMnemonicsID</h1>

<p align="center">
  <b>Well log mnemonic identification using lasio and dlisio</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/lasmnemonicsid/"><img src="https://img.shields.io/pypi/v/lasmnemonicsid.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/lasmnemonicsid/"><img src="https://img.shields.io/pypi/pyversions/lasmnemonicsid.svg" alt="Python Versions"></a>
  <a href="https://github.com/Nobleza-Energy/LASMnemonicsID/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Nobleza-Energy/LASMnemonicsID.svg" alt="License"></a>
</p>

---

## 📦 Installation

```bash
pip install lasmnemonicsid
```



## 🚀 QuickStart
```
from LASMnemonicsID.LAS import parseLAS

# Load LAS file
df = parseLAS("your_well.las")
print(df.head())
```

## 🧪 Test with your Data
```
from LASMnemonicsID.LAS import parseLAS

# Load and inspect
df = parseLAS("path/to/well.las")
print(f"✅ {len(df)} rows, {len(df.columns)} curves")
print(df.columns.tolist())
```
