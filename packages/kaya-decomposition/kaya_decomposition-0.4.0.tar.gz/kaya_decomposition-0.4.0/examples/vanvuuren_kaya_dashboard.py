#!/usr/bin/env python3
"""
Van Vuuren IMAGE Kaya Decomposition Dashboard

This script recreates the dashboards from the Excel workbook:
    vanVuurenIMAGE_15_TOT_19_TFC_currentcopy.xlsm

It demonstrates how to:
1. Connect to the IIASA database using pyam
2. Download scenario data for IMAGE 3.0.1 model
3. Compute Kaya decomposition factors and ratios
4. Visualize results matching the Excel dashboard style

Recreated figures:
- Fig3ExpandKAYAfactorsDEq: Kaya factors (P, GNP, FE, PEDEq, PEFF, TFC, NFC)
- Fig4ExpandKAYAratiosDEq: Kaya ratios (GNP/P, FE/GNP, PEDEq/FE, etc.)

Data source:
- IAMC 1.5°C Scenario Explorer (iamc15)
- Model: IMAGE 3.0.1
- Reference Scenario: SSP2-Baseline
- Intervention Scenario: IMA15-TOT
- Region: World
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyam

from kaya_decomposition import (
    compute_kaya_factors,
    compute_kaya_variables,
    input_variables,
    kaya_factors as kf,
    kaya_variables as kv,
)

warnings.filterwarnings("ignore")

# =============================================================================
# Configuration
# =============================================================================

# IIASA Database settings
DATABASE = "iamc15"
MODEL = "IMAGE 3.0.1"
REF_SCENARIO = "SSP2-Baseline"
INT_SCENARIO = "IMA15-TOT"
REGION = "World"
BASE_YEAR = 2010  # Index year for normalized plots

# Required variables for Kaya decomposition
REQUIRED_VARIABLES = [
    "Population",
    "GDP|PPP",
    "GDP|MER",
    "Final Energy",
    "Primary Energy",
    "Primary Energy|Coal",
    "Primary Energy|Oil",
    "Primary Energy|Gas",
    "Emissions|CO2|Energy and Industrial Processes",
    "Emissions|CO2|Industrial Processes",
    "Emissions|CO2|AFOLU",
    "Emissions|CH4",
    "Emissions|N2O",
    "Emissions|F-Gases",
    "Carbon Sequestration|CCS",
    "Carbon Sequestration|CCS|Biomass",
    "Carbon Sequestration|CCS|Fossil|Energy",
    "Carbon Sequestration|CCS|Fossil|Industrial Processes",
    "Carbon Sequestration|CCS|Biomass|Energy",
    "Carbon Sequestration|CCS|Biomass|Industrial Processes",
]

# Color scheme for plots (matching Excel dashboard aesthetic)
COLORS = {
    "P": "#2E86AB",  # Population - blue
    "GNP": "#A23B72",  # GDP - magenta
    "FE": "#F18F01",  # Final Energy - orange
    "PEDEq": "#C73E1D",  # Primary Energy - red
    "PEFF": "#3B1F2B",  # Fossil Energy - dark
    "TFC": "#6B4226",  # Total Fossil Carbon - brown
    "NFC": "#228B22",  # Net Fossil Carbon - green
    "ref": "#1f77b4",  # Reference scenario - blue
    "int": "#ff7f0e",  # Intervention scenario - orange
}


# =============================================================================
# Data Loading Functions
# =============================================================================


def download_data_from_iiasa(
    database: str = DATABASE,
    model: str = MODEL,
    scenarios: list = None,
    region: str = REGION,
    variables: list = None,
) -> pyam.IamDataFrame:
    """
    Download scenario data from the IIASA database.

    Parameters
    ----------
    database : str
        Name of the IIASA database (e.g., 'iamc15')
    model : str
        Model name (e.g., 'IMAGE 3.0.1')
    scenarios : list
        List of scenario names
    region : str
        Region to filter (e.g., 'World')
    variables : list
        List of variables to download

    Returns
    -------
    pyam.IamDataFrame
        Downloaded data
    """
    if scenarios is None:
        scenarios = [REF_SCENARIO, INT_SCENARIO]
    if variables is None:
        variables = REQUIRED_VARIABLES

    print(f"Connecting to IIASA database: {database}")
    print(f"  Model: {model}")
    print(f"  Scenarios: {scenarios}")
    print(f"  Region: {region}")
    print(f"  Variables: {len(variables)} requested")

    df = pyam.read_iiasa(
        database,
        model=model,
        scenario=scenarios,
        region=region,
        variable=variables,
    )

    print(f"\nDownloaded {len(df.data)} data points")
    print(f"  Years: {sorted(df.year)}")
    print(f"  Variables found: {len(df.variable)}")

    return df


def prepare_data_for_kaya(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """
    Prepare downloaded data for Kaya decomposition.

    The kaya-decomposition library now accepts IIASA variable names directly.
    This function only handles unit normalization and filling missing variables.

    Parameters
    ----------
    df : pyam.IamDataFrame
        Raw data from IIASA

    Returns
    -------
    pyam.IamDataFrame
        Data ready for Kaya analysis
    """
    # Create a copy of the data
    data = df.data.copy()

    # Normalize units to avoid pint parsing issues
    # The library expects simple units without scaling factors in the unit string
    unit_mapping = {
        "billion US$2010/yr": "billion USD_2010/yr",
        "billion US$2005/yr": "billion USD_2005/yr",
    }
    for old_unit, new_unit in unit_mapping.items():
        data.loc[data["unit"] == old_unit, "unit"] = new_unit

    # Get unique combinations for filling missing variables
    scenarios = data[["model", "scenario", "region"]].drop_duplicates()
    years = data["year"].unique()

    # Variables that should be filled with zeros if missing
    zero_fill_vars = [
        "Carbon Sequestration|CCS",
        "Carbon Sequestration|CCS|Biomass",
        "Carbon Sequestration|CCS|Fossil|Energy",
        "Carbon Sequestration|CCS|Fossil|Industrial Processes",
        "Carbon Sequestration|CCS|Biomass|Energy",
        "Carbon Sequestration|CCS|Biomass|Industrial Processes",
        "Emissions|CO2|Industrial Processes",
    ]

    for _, row in scenarios.iterrows():
        for var in zero_fill_vars:
            existing = data[
                (data["model"] == row["model"])
                & (data["scenario"] == row["scenario"])
                & (data["region"] == row["region"])
                & (data["variable"] == var)
            ]
            if len(existing) == 0:
                # Add zero values for this variable
                new_rows = []
                for year in years:
                    new_rows.append(
                        {
                            "model": row["model"],
                            "scenario": row["scenario"],
                            "region": row["region"],
                            "variable": var,
                            "unit": "Mt CO2/yr",
                            "year": year,
                            "value": 0.0,
                        }
                    )
                data = pd.concat([data, pd.DataFrame(new_rows)], ignore_index=True)

    return pyam.IamDataFrame(data)


# =============================================================================
# Kaya Computation Functions
# =============================================================================


def compute_kaya_for_scenario(
    df: pyam.IamDataFrame, scenario: str
) -> tuple[pyam.IamDataFrame, pyam.IamDataFrame]:
    """
    Compute Kaya variables and factors for a single scenario.

    Parameters
    ----------
    df : pyam.IamDataFrame
        Input data
    scenario : str
        Scenario name to analyze

    Returns
    -------
    tuple
        (kaya_variables, kaya_factors) as IamDataFrames
    """
    scenario_data = df.filter(scenario=scenario)

    kaya_vars = compute_kaya_variables(scenario_data)
    if kaya_vars is None:
        raise ValueError(f"Could not compute Kaya variables for scenario: {scenario}")

    kaya_facs = compute_kaya_factors(kaya_vars)

    return kaya_vars, kaya_facs


def extract_factors_timeseries(
    kaya_vars: pyam.IamDataFrame, kaya_factors: pyam.IamDataFrame
) -> pd.DataFrame:
    """
    Extract Kaya factors as a timeseries DataFrame.

    Returns DataFrame with columns: year, P, GNP, FE, PEDEq, PEFF, TFC, NFC
    """
    # Get timeseries data
    ts = kaya_vars.timeseries()

    # Extract each factor
    factors = {}

    # Population (in billions)
    pop_data = kaya_vars.filter(variable=input_variables.POPULATION).data
    factors["P"] = {int(r["year"]): r["value"] / 1000 for _, r in pop_data.iterrows()}

    # GDP (in trillions USD)
    gdp_data = kaya_vars.filter(variable=input_variables.GDP_PPP).data
    factors["GNP"] = {int(r["year"]): r["value"] / 1000 for _, r in gdp_data.iterrows()}

    # Final Energy (EJ)
    fe_data = kaya_vars.filter(variable=input_variables.FINAL_ENERGY).data
    factors["FE"] = {int(r["year"]): r["value"] for _, r in fe_data.iterrows()}

    # Primary Energy (EJ)
    pe_data = kaya_vars.filter(variable=input_variables.PRIMARY_ENERGY).data
    factors["PEDEq"] = {int(r["year"]): r["value"] for _, r in pe_data.iterrows()}

    # Primary Energy Fossil (EJ)
    peff_data = kaya_vars.filter(variable=kv.PRIMARY_ENERGY_FF).data
    factors["PEFF"] = {int(r["year"]): r["value"] for _, r in peff_data.iterrows()}

    # Total Fossil Carbon (Gt CO2)
    tfc_data = kaya_vars.filter(variable=kv.TFC).data
    factors["TFC"] = {int(r["year"]): r["value"] / 1000 for _, r in tfc_data.iterrows()}

    # Net Fossil Carbon (Gt CO2)
    nfc_data = kaya_vars.filter(variable=kv.NFC).data
    factors["NFC"] = {int(r["year"]): r["value"] / 1000 for _, r in nfc_data.iterrows()}

    # Convert to DataFrame
    years = sorted(set.union(*[set(v.keys()) for v in factors.values()]))
    result = pd.DataFrame({"year": years})

    for name, values in factors.items():
        result[name] = result["year"].map(values)

    return result.set_index("year")


def extract_ratios_timeseries(kaya_factors: pyam.IamDataFrame) -> pd.DataFrame:
    """
    Extract Kaya ratios as a timeseries DataFrame.

    Returns DataFrame with columns: year, GNP/P, FE/GNP, PEDEq/FE, PEFF/PEDEq, TFC/PEFF, NFC/TFC
    """
    ratios = {}

    # GNP/P (USD/person) - scale from thousand USD to USD
    data = kaya_factors.filter(variable=kf.GNP_per_P).data
    ratios["GNP/P"] = {int(r["year"]): r["value"] * 1000 for _, r in data.iterrows()}

    # FE/GNP (EJ/trillion USD) - scale from EJ/billion USD
    data = kaya_factors.filter(variable=kf.FE_per_GNP).data
    ratios["FE/GNP"] = {int(r["year"]): r["value"] * 1000 for _, r in data.iterrows()}

    # PEDEq/FE (dimensionless)
    data = kaya_factors.filter(variable=kf.PEdeq_per_FE).data
    ratios["PEDEq/FE"] = {int(r["year"]): r["value"] for _, r in data.iterrows()}

    # PEFF/PEDEq (dimensionless)
    data = kaya_factors.filter(variable=kf.PEFF_per_PEDEq).data
    ratios["PEFF/PEDEq"] = {int(r["year"]): r["value"] for _, r in data.iterrows()}

    # TFC/PEFF (Mt CO2/EJ)
    data = kaya_factors.filter(variable=kf.TFC_per_PEFF).data
    ratios["TFC/PEFF"] = {int(r["year"]): r["value"] for _, r in data.iterrows()}

    # NFC/TFC (dimensionless)
    data = kaya_factors.filter(variable=kf.NFC_per_TFC).data
    ratios["NFC/TFC"] = {int(r["year"]): r["value"] for _, r in data.iterrows()}

    # Convert to DataFrame
    years = sorted(set.union(*[set(v.keys()) for v in ratios.values()]))
    result = pd.DataFrame({"year": years})

    for name, values in ratios.items():
        result[name] = result["year"].map(values)

    return result.set_index("year")


# =============================================================================
# Visualization Functions
# =============================================================================


def plot_kaya_factors_dashboard(
    ref_factors: pd.DataFrame,
    int_factors: pd.DataFrame,
    base_year: int = BASE_YEAR,
    title: str = "Drivers of Global Emissions from the Energy Sector",
    model: str = MODEL,
    ref_scenario: str = REF_SCENARIO,
    int_scenario: str = INT_SCENARIO,
) -> plt.Figure:
    """
    Create the Fig3ExpandKAYAfactorsDEq dashboard.

    This shows the absolute Kaya factors (P, GNP, FE, PEDEq, PEFF, TFC, NFC)
    for both reference and intervention scenarios.

    Parameters
    ----------
    ref_factors : pd.DataFrame
        Reference scenario factors from extract_factors_timeseries
    int_factors : pd.DataFrame
        Intervention scenario factors from extract_factors_timeseries
    base_year : int
        Year to use for indexing (normalization)
    title : str
        Dashboard title
    model : str
        Model name for subtitle
    ref_scenario : str
        Reference scenario name
    int_scenario : str
        Intervention scenario name

    Returns
    -------
    plt.Figure
        Matplotlib figure
    """
    factor_names = ["P", "GNP", "FE", "PEDEq", "PEFF", "TFC", "NFC"]
    factor_labels = {
        "P": "Population\n(billions)",
        "GNP": "GDP\n(trillion USD)",
        "FE": "Final Energy\n(EJ/yr)",
        "PEDEq": "Primary Energy\n(EJ/yr)",
        "PEFF": "Fossil Energy\n(EJ/yr)",
        "TFC": "Total Fossil C\n(Gt CO2/yr)",
        "NFC": "Net Fossil C\n(Gt CO2/yr)",
    }

    # Create figure with 7 subplots (2 rows)
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor("#f8f9fa")

    # Add title and subtitle
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.94,
        f"Model: {model}  |  Reference: {ref_scenario}  |  Intervention: {int_scenario}",
        ha="center",
        fontsize=11,
        color="#666",
    )

    # Create grid for subplots
    gs = fig.add_gridspec(2, 4, hspace=0.35, wspace=0.3, top=0.88, bottom=0.08)

    # Plot each factor
    for i, factor in enumerate(factor_names):
        if i < 4:
            ax = fig.add_subplot(gs[0, i])
        else:
            ax = fig.add_subplot(gs[1, i - 4])

        ax.set_facecolor("#ffffff")

        # Plot reference scenario
        ax.plot(
            ref_factors.index,
            ref_factors[factor],
            color=COLORS["ref"],
            linewidth=2.5,
            label="Reference",
            marker="o",
            markersize=4,
        )

        # Plot intervention scenario
        ax.plot(
            int_factors.index,
            int_factors[factor],
            color=COLORS["int"],
            linewidth=2.5,
            label="Intervention",
            marker="s",
            markersize=4,
        )

        ax.set_title(factor_labels[factor], fontsize=10, fontweight="bold", pad=10)
        ax.set_xlabel("Year", fontsize=9)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.tick_params(axis="both", labelsize=8)

        # Add legend to first subplot only
        if i == 0:
            ax.legend(loc="upper left", fontsize=8)

        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Hide the last empty subplot
    ax_empty = fig.add_subplot(gs[1, 3])
    ax_empty.axis("off")

    return fig


def plot_kaya_ratios_dashboard(
    ref_ratios: pd.DataFrame,
    int_ratios: pd.DataFrame,
    ref_factors: pd.DataFrame,
    int_factors: pd.DataFrame,
    base_year: int = BASE_YEAR,
    title: str = "Drivers of Global Emissions from the Energy Sector - Ratios",
    model: str = MODEL,
    ref_scenario: str = REF_SCENARIO,
    int_scenario: str = INT_SCENARIO,
) -> plt.Figure:
    """
    Create the Fig4ExpandKAYAratiosDEq dashboard.

    This shows the Kaya ratios (P, GNP/P, FE/GNP, PEDEq/FE, PEFF/PEDEq, TFC/PEFF, NFC/TFC)
    for both reference and intervention scenarios.

    Parameters
    ----------
    ref_ratios : pd.DataFrame
        Reference scenario ratios from extract_ratios_timeseries
    int_ratios : pd.DataFrame
        Intervention scenario ratios from extract_ratios_timeseries
    ref_factors : pd.DataFrame
        Reference scenario factors (for Population)
    int_factors : pd.DataFrame
        Intervention scenario factors (for Population)
    base_year : int
        Year to use for indexing
    title : str
        Dashboard title
    model : str
        Model name for subtitle
    ref_scenario : str
        Reference scenario name
    int_scenario : str
        Intervention scenario name

    Returns
    -------
    plt.Figure
        Matplotlib figure
    """
    # Combine Population with ratios
    ratio_names = ["P", "GNP/P", "FE/GNP", "PEDEq/FE", "PEFF/PEDEq", "TFC/PEFF", "NFC/TFC"]
    ratio_labels = {
        "P": "Population\n(billions)",
        "GNP/P": "GDP per Capita\n(USD/person)",
        "FE/GNP": "Energy Intensity\n(EJ/trillion USD)",
        "PEDEq/FE": "PE/FE Ratio\n(dimensionless)",
        "PEFF/PEDEq": "Fossil Share\n(dimensionless)",
        "TFC/PEFF": "Carbon Intensity\n(Mt CO2/EJ)",
        "NFC/TFC": "Net/Total Carbon\n(dimensionless)",
    }

    # Create figure with 7 subplots (2 rows)
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor("#f8f9fa")

    # Add title and subtitle
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.94,
        f"Model: {model}  |  Reference: {ref_scenario}  |  Intervention: {int_scenario}",
        ha="center",
        fontsize=11,
        color="#666",
    )

    # Create grid for subplots
    gs = fig.add_gridspec(2, 4, hspace=0.35, wspace=0.3, top=0.88, bottom=0.08)

    # Plot each ratio
    for i, ratio in enumerate(ratio_names):
        if i < 4:
            ax = fig.add_subplot(gs[0, i])
        else:
            ax = fig.add_subplot(gs[1, i - 4])

        ax.set_facecolor("#ffffff")

        # Get data (Population comes from factors, rest from ratios)
        if ratio == "P":
            ref_data = ref_factors["P"]
            int_data = int_factors["P"]
        else:
            ref_data = ref_ratios[ratio]
            int_data = int_ratios[ratio]

        # Plot reference scenario
        ax.plot(
            ref_data.index,
            ref_data,
            color=COLORS["ref"],
            linewidth=2.5,
            label="Reference",
            marker="o",
            markersize=4,
        )

        # Plot intervention scenario
        ax.plot(
            int_data.index,
            int_data,
            color=COLORS["int"],
            linewidth=2.5,
            label="Intervention",
            marker="s",
            markersize=4,
        )

        ax.set_title(ratio_labels[ratio], fontsize=10, fontweight="bold", pad=10)
        ax.set_xlabel("Year", fontsize=9)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.tick_params(axis="both", labelsize=8)

        # Add legend to first subplot only
        if i == 0:
            ax.legend(loc="upper left", fontsize=8)

        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Hide the last empty subplot
    ax_empty = fig.add_subplot(gs[1, 3])
    ax_empty.axis("off")

    return fig


def plot_indexed_factors_dashboard(
    ref_factors: pd.DataFrame,
    int_factors: pd.DataFrame,
    base_year: int = BASE_YEAR,
    title: str = "Kaya Factors - Indexed to Base Year",
    model: str = MODEL,
    ref_scenario: str = REF_SCENARIO,
    int_scenario: str = INT_SCENARIO,
) -> plt.Figure:
    """
    Create an indexed version of the Kaya factors dashboard.

    All factors are normalized to their base year values (index = 1.0).

    Parameters
    ----------
    ref_factors : pd.DataFrame
        Reference scenario factors
    int_factors : pd.DataFrame
        Intervention scenario factors
    base_year : int
        Year to use for indexing (normalization)
    title : str
        Dashboard title
    model : str
        Model name
    ref_scenario : str
        Reference scenario name
    int_scenario : str
        Intervention scenario name

    Returns
    -------
    plt.Figure
        Matplotlib figure
    """
    factor_names = ["P", "GNP", "FE", "PEDEq", "PEFF", "TFC", "NFC"]
    factor_labels = {
        "P": "Population",
        "GNP": "GDP",
        "FE": "Final Energy",
        "PEDEq": "Primary Energy",
        "PEFF": "Fossil Energy",
        "TFC": "Total Fossil Carbon",
        "NFC": "Net Fossil Carbon",
    }

    # Normalize to base year
    ref_indexed = ref_factors.copy()
    int_indexed = int_factors.copy()

    for factor in factor_names:
        if base_year in ref_factors.index:
            base_val = ref_factors.loc[base_year, factor]
            if base_val != 0:
                ref_indexed[factor] = ref_factors[factor] / base_val
                int_indexed[factor] = int_factors[factor] / base_val

    # Create figure
    fig, axes = plt.subplots(2, 4, figsize=(18, 10))
    fig.patch.set_facecolor("#f8f9fa")

    fig.suptitle(f"{title} (Base Year = {base_year})", fontsize=16, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.94,
        f"Model: {model}  |  Reference: {ref_scenario}  |  Intervention: {int_scenario}",
        ha="center",
        fontsize=11,
        color="#666",
    )

    axes = axes.flatten()

    for i, factor in enumerate(factor_names):
        ax = axes[i]
        ax.set_facecolor("#ffffff")

        # Plot reference
        ax.plot(
            ref_indexed.index,
            ref_indexed[factor],
            color=COLORS["ref"],
            linewidth=2.5,
            label="Reference",
            marker="o",
            markersize=4,
        )

        # Plot intervention
        ax.plot(
            int_indexed.index,
            int_indexed[factor],
            color=COLORS["int"],
            linewidth=2.5,
            label="Intervention",
            marker="s",
            markersize=4,
        )

        # Add horizontal line at 1.0
        ax.axhline(y=1.0, color="#999", linestyle="--", linewidth=1, alpha=0.5)

        ax.set_title(factor_labels[factor], fontsize=10, fontweight="bold", pad=10)
        ax.set_xlabel("Year", fontsize=9)
        ax.set_ylabel(f"Index ({base_year} = 1.0)", fontsize=9)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.tick_params(axis="both", labelsize=8)

        if i == 0:
            ax.legend(loc="upper left", fontsize=8)

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Hide last subplot
    axes[7].axis("off")

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    return fig


# =============================================================================
# Main Execution
# =============================================================================


def main():
    """Main function to run the dashboard generation."""
    print("=" * 70)
    print("Van Vuuren IMAGE Kaya Decomposition Dashboard")
    print("=" * 70)
    print()

    # Step 1: Download data from IIASA
    print("Step 1: Downloading data from IIASA database...")
    print("-" * 50)

    try:
        raw_data = download_data_from_iiasa()
    except Exception as e:
        print(f"\nError downloading data: {e}")
        print("\nPlease ensure you have internet access and the pyam package")
        print("is properly configured to access the IIASA database.")
        return

    # Step 2: Prepare data for Kaya analysis
    print("\nStep 2: Preparing data for Kaya analysis...")
    print("-" * 50)

    prepared_data = prepare_data_for_kaya(raw_data)
    print(f"Prepared data has {len(prepared_data.variable)} variables")

    # Step 3: Compute Kaya factors for both scenarios
    print("\nStep 3: Computing Kaya decomposition...")
    print("-" * 50)

    print(f"  Computing for Reference scenario: {REF_SCENARIO}")
    ref_kaya_vars, ref_kaya_factors = compute_kaya_for_scenario(prepared_data, REF_SCENARIO)

    print(f"  Computing for Intervention scenario: {INT_SCENARIO}")
    int_kaya_vars, int_kaya_factors = compute_kaya_for_scenario(prepared_data, INT_SCENARIO)

    # Step 4: Extract timeseries data
    print("\nStep 4: Extracting timeseries data...")
    print("-" * 50)

    ref_factors = extract_factors_timeseries(ref_kaya_vars, ref_kaya_factors)
    int_factors = extract_factors_timeseries(int_kaya_vars, int_kaya_factors)

    ref_ratios = extract_ratios_timeseries(ref_kaya_factors)
    int_ratios = extract_ratios_timeseries(int_kaya_factors)

    print("Reference scenario factors:")
    print(ref_factors.round(2))
    print("\nIntervention scenario factors:")
    print(int_factors.round(2))

    # Step 5: Create visualizations
    print("\nStep 5: Creating dashboard visualizations...")
    print("-" * 50)

    # Create output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Fig3: Kaya Factors Dashboard
    print("  Creating Fig3: Kaya Factors Dashboard...")
    fig3 = plot_kaya_factors_dashboard(ref_factors, int_factors)
    fig3.savefig(output_dir / "fig3_kaya_factors.png", dpi=150, bbox_inches="tight")
    fig3.savefig(output_dir / "fig3_kaya_factors.pdf", bbox_inches="tight")
    print(f"    Saved to: {output_dir / 'fig3_kaya_factors.png'}")

    # Fig4: Kaya Ratios Dashboard
    print("  Creating Fig4: Kaya Ratios Dashboard...")
    fig4 = plot_kaya_ratios_dashboard(ref_ratios, int_ratios, ref_factors, int_factors)
    fig4.savefig(output_dir / "fig4_kaya_ratios.png", dpi=150, bbox_inches="tight")
    fig4.savefig(output_dir / "fig4_kaya_ratios.pdf", bbox_inches="tight")
    print(f"    Saved to: {output_dir / 'fig4_kaya_ratios.png'}")

    # Bonus: Indexed Factors Dashboard
    print("  Creating Indexed Factors Dashboard...")
    fig_indexed = plot_indexed_factors_dashboard(ref_factors, int_factors)
    fig_indexed.savefig(output_dir / "fig_indexed_factors.png", dpi=150, bbox_inches="tight")
    print(f"    Saved to: {output_dir / 'fig_indexed_factors.png'}")

    # Step 6: Save data to CSV
    print("\nStep 6: Saving data to CSV...")
    print("-" * 50)

    ref_factors.to_csv(output_dir / "ref_kaya_factors.csv")
    int_factors.to_csv(output_dir / "int_kaya_factors.csv")
    ref_ratios.to_csv(output_dir / "ref_kaya_ratios.csv")
    int_ratios.to_csv(output_dir / "int_kaya_ratios.csv")
    print(f"  Saved CSV files to: {output_dir}")

    print("\n" + "=" * 70)
    print("Dashboard generation complete!")
    print("=" * 70)

    # Show plots
    plt.show()


if __name__ == "__main__":
    main()
