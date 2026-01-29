# Kaya Decomposition Examples

This directory contains example scripts and notebooks demonstrating how to use the `kaya-decomposition` library with data from the IIASA database.

## Interactive Tutorial (Recommended for Learning)

**Notebook:** `kaya_dashboard_tutorial.ipynb`

A step-by-step Jupyter notebook that walks through the entire process of:
- Connecting to the IIASA database
- Downloading scenario data
- Computing Kaya decomposition
- Creating visualizations

Great for learning and experimentation. Run with:

```bash
jupyter notebook examples/kaya_dashboard_tutorial.ipynb
```

## Automated Dashboard Script

**Script:** `vanvuuren_kaya_dashboard.py`

This script recreates the Kaya decomposition dashboards from the Excel workbook `vanVuurenIMAGE_15_TOT_19_TFC_currentcopy.xlsm`.

### Features

- Connects to the IIASA database using `pyam`
- Downloads scenario data for the IMAGE 3.0.1 model
- Computes Kaya decomposition factors and ratios
- Creates publication-quality visualizations

### Recreated Figures

1. **Fig3: Kaya Factors Dashboard** (`fig3_kaya_factors.png`)
   - Population (P)
   - GDP (GNP)
   - Final Energy (FE)
   - Primary Energy (PEDEq)
   - Fossil Energy (PEFF)
   - Total Fossil Carbon (TFC)
   - Net Fossil Carbon (NFC)

2. **Fig4: Kaya Ratios Dashboard** (`fig4_kaya_ratios.png`)
   - Population (P)
   - GDP per Capita (GNP/P)
   - Energy Intensity (FE/GNP)
   - PE/FE Ratio (PEDEq/FE)
   - Fossil Share (PEFF/PEDEq)
   - Carbon Intensity (TFC/PEFF)
   - Net/Total Carbon (NFC/TFC)

3. **Indexed Factors Dashboard** (`fig_indexed_factors.png`)
   - All factors normalized to base year (2010 = 1.0)

### Data Source

- **Database:** IAMC 1.5°C Scenario Explorer (iamc15)
- **Model:** IMAGE 3.0.1
- **Reference Scenario:** SSP2-Baseline
- **Intervention Scenario:** IMA15-TOT
- **Region:** World

### Running the Example

```bash
# From the kaya-decomposition root directory
python examples/vanvuuren_kaya_dashboard.py
```

### Requirements

- Internet connection (to download data from IIASA)
- `pyam-iamc` package
- `matplotlib` for visualization

### Output

The script creates the following files in `examples/output/`:

- `fig3_kaya_factors.png` / `.pdf` - Kaya factors dashboard
- `fig4_kaya_ratios.png` / `.pdf` - Kaya ratios dashboard
- `fig_indexed_factors.png` - Indexed factors dashboard
- `ref_kaya_factors.csv` - Reference scenario factors data
- `int_kaya_factors.csv` - Intervention scenario factors data
- `ref_kaya_ratios.csv` - Reference scenario ratios data
- `int_kaya_ratios.csv` - Intervention scenario ratios data

## Understanding the Kaya Identity

The Kaya identity decomposes CO2 emissions into contributing factors:

```
CO2 = P × (GDP/P) × (FE/GDP) × (PE/FE) × (PEFF/PE) × (TFC/PEFF) × (NFC/TFC)
```

Where:
- **P** = Population
- **GDP/P** = GDP per capita (economic activity per person)
- **FE/GDP** = Energy intensity of the economy
- **PE/FE** = Primary to final energy ratio (energy supply losses)
- **PEFF/PE** = Fossil fuel fraction of primary energy
- **TFC/PEFF** = Carbon intensity of fossil energy
- **NFC/TFC** = Net to total carbon ratio (accounts for CCS)

This decomposition allows analysis of which factors drive emissions changes over time or between scenarios.
