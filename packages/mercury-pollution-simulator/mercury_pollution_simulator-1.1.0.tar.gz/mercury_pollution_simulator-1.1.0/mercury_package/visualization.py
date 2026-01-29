"""
Visualization functions for mercury pollution simulation results
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from typing import Dict


def generate_all_plots(
    results: Dict,
    validation: Dict,
    probs: Dict,
    sens: Dict,
    time_points: np.ndarray,
    output_dir: str,
    model=None,
):
    """
    Generate all visualization plots for the simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results dictionary
    validation : dict
        Model validation results
    probs : dict
        Risk probability calculations
    sens : dict
        Sensitivity analysis results
    time_points : array-like
        Time points used in simulation (days)
    output_dir : str
        Directory to save plots
    model : EmpiricalMercuryModel, optional
        Model instance to use for predictions
    """
    print("\nGenerating visualizations...")
    
    # 1. Validation Plot
    plot_validation(results, validation, output_dir, model=model)
    
    # 2. Transport Schematic with Data
    plot_transport_diagram(results, output_dir)
    
    # 3. Accumulation Time Series
    plot_accumulation(results, time_points, output_dir)
    
    # 4. Risk Dashboard
    plot_risk_dashboard(results, probs, time_points, output_dir)
    
    # 5. Sensitivity Plot
    plot_sensitivity(sens, output_dir)
    
    # 6. Comprehensive Summary Figure
    plot_summary(results, validation, probs, time_points, output_dir)
    
    print("All visualizations saved.")


def plot_validation(results: Dict, validation: Dict, output_dir: str, model=None):
    """Plot model validation"""
    from mercury_package.models.empirical_model import EmpiricalMercuryModel
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    time_dense = np.linspace(0, max(results["time"]), 200)
    if model is None:
        model = EmpiricalMercuryModel()
    
    configs = [
        ("water", "Water Mercury (mg/L)", "blue"),
        ("sediment", "Sediment Mercury (mg/kg)", "brown"),
        ("topsoil", "Topsoil Mercury (mg/kg)", "green"),
        ("subsoil", "Subsoil Mercury (mg/kg)", "olive")
    ]
    
    for ax, (comp, ylabel, color) in zip(axes.flat, configs):
        # Model prediction
        if comp == "water":
            pred = model.predict_water(time_dense)
        elif comp == "sediment":
            pred = model.predict_sediment(time_dense)
        elif comp == "topsoil":
            pred = model.predict_topsoil(time_dense)
        else:
            pred = model.predict_subsoil(time_dense)
            
        ax.plot(time_dense/365, pred, color=color, linewidth=2, label='Model')
        
        # Observations
        v = validation[comp]
        ax.scatter(np.array(v['times'])/365, v['observed'], s=100, c='red', 
                  marker='o', label='Observed', zorder=5, edgecolors='black')
        
        ax.set_xlabel('Time (years)', fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(f'{comp.title()}: R² = {v["r2"]:.3f}', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_dense)/365 + 0.2)
        
    plt.suptitle('Model Validation: Calibrated to Field Data', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/01_model_validation.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 01_model_validation.png")


def plot_transport_diagram(results: Dict, output_dir: str):
    """Plot transport schematic with quantitative data"""
    fig = plt.figure(figsize=(14, 10))
    
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Boxes
    boxes = {
        'source': ([4, 9], 2, 0.8, 'Mercury Source\n(Amalgamation)', 'gold'),
        'water': ([3, 7], 4, 1.5, '', 'lightblue'),
        'sediment': ([1, 4.5], 2.5, 1.5, '', 'burlywood'),
        'soil': ([6, 4.5], 3, 1.5, '', 'lightgreen'),
    }
    
    for key, (pos, w, h, label, color) in boxes.items():
        rect = plt.Rectangle(pos, w, h, facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        if label:
            ax.text(pos[0]+w/2, pos[1]+h/2, label, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Add data to boxes
    water_peak = np.max(np.mean(results["water"], axis=1))
    water_y5 = np.mean(results["water"][-1, :])
    sed_y5 = np.mean(results["sediment"][-1, :])
    soil_y5 = np.mean(results["topsoil"][-1, :])
    
    ax.text(5, 7.7, 'WATER COLUMN', ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax.text(5, 7.0, f'Peak: {water_peak:.3f} mg/L\nYear 5: {water_y5:.3f} mg/L', 
           ha='center', va='center', fontsize=10)
    
    ax.text(2.25, 5.7, 'SEDIMENT', ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax.text(2.25, 5.0, f'Year 5:\n{sed_y5:.2f} mg/kg', ha='center', va='center', fontsize=10)
    
    ax.text(7.5, 5.7, 'FLOODPLAIN SOIL', ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax.text(7.5, 5.0, f'Year 5:\n{soil_y5:.2f} mg/kg', ha='center', va='center', fontsize=10)
    
    # Arrows
    ax.annotate('', xy=(5, 8.5), xytext=(5, 9), 
               arrowprops=dict(arrowstyle='->', lw=2, color='red'))
    ax.text(5.5, 8.7, 'Release', fontsize=9, color='red')
    
    ax.annotate('', xy=(3, 6), xytext=(3.5, 7), 
               arrowprops=dict(arrowstyle='->', lw=2, color='brown'))
    ax.text(2.2, 6.5, 'Settling', fontsize=9, rotation=60)
    
    ax.annotate('', xy=(7, 6), xytext=(6.5, 7), 
               arrowprops=dict(arrowstyle='->', lw=2, color='green'))
    ax.text(7.2, 6.5, 'Flooding', fontsize=9, rotation=-60)
    
    ax.annotate('', xy=(9, 7.5), xytext=(7, 7.5), 
               arrowprops=dict(arrowstyle='->', lw=2, color='blue'))
    ax.text(8, 7.8, 'Outflow', fontsize=9)
    
    ax.set_title('Mercury Transport Pathways', fontsize=14, fontweight='bold', pad=20)
    
    plt.savefig(f"{output_dir}/02_transport_diagram.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 02_transport_diagram.png")


def plot_accumulation(results: Dict, time_points: np.ndarray, output_dir: str):
    """Plot accumulation time series"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    time_years = time_points / 365
    
    configs = [
        ("water", "Water Mercury (mg/L)", "blue", 0.002, "EPA MCL"),
        ("sediment", "Sediment Mercury (mg/kg)", "brown", 1.06, "PEC"),
        ("topsoil", "Topsoil Mercury (mg/kg)", "green", 1.0, "Agri."),
        ("subsoil", "Subsoil Mercury (mg/kg)", "olive", None, None)
    ]
    
    for ax, (key, ylabel, color, thresh, thresh_label) in zip(axes.flat, configs):
        data = results[key]
        
        # Uncertainty bands
        ax.fill_between(time_years, np.percentile(data, 5, axis=1),
                       np.percentile(data, 95, axis=1), alpha=0.2, color=color, label='90% CI')
        ax.fill_between(time_years, np.percentile(data, 25, axis=1),
                       np.percentile(data, 75, axis=1), alpha=0.3, color=color, label='50% CI')
        
        # Mean and median
        ax.plot(time_years, np.mean(data, axis=1), color=color, linewidth=2, 
               linestyle='--', label='Mean')
        ax.plot(time_years, np.median(data, axis=1), color=color, linewidth=2, label='Median')
        
        # Threshold
        if thresh:
            ax.axhline(thresh, color='red', linestyle=':', linewidth=2, label=thresh_label)
            
        ax.set_xlabel('Time (years)', fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(f'{key.title()} Accumulation', fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_years))
        
    plt.suptitle('Mercury Accumulation Over Time (Monte Carlo Uncertainty)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/03_accumulation_timeseries.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 03_accumulation_timeseries.png")


def plot_risk_dashboard(results: Dict, probs: Dict, time_points: np.ndarray, output_dir: str):
    """Create risk assessment dashboard"""
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)
    
    # 1. Exceedance probabilities
    ax1 = fig.add_subplot(gs[0, :2])
    categories = list(probs.keys())
    values = list(probs.values())
    colors = ['green' if v < 25 else 'orange' if v < 75 else 'red' for v in values]
    
    ax1.barh(range(len(categories)), values, color=colors, edgecolor='black')
    ax1.set_yticks(range(len(categories)))
    ax1.set_yticklabels(categories, fontsize=9)
    ax1.set_xlabel('Exceedance Probability (%)')
    ax1.set_title('Regulatory Threshold Exceedance', fontsize=12, fontweight='bold')
    ax1.axvline(25, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(75, color='gray', linestyle='--', alpha=0.5)
    ax1.set_xlim(0, 100)
    
    # 2. HQ Distribution
    ax2 = fig.add_subplot(gs[0, 2])
    hq = results["hazard_quotient"][-1, :]
    ax2.hist(hq, bins=50, density=True, color='coral', edgecolor='black', alpha=0.7)
    ax2.axvline(1.0, color='red', linestyle='--', linewidth=2, label='HQ=1')
    ax2.axvline(np.mean(hq), color='blue', linestyle='-', linewidth=2, label=f'Mean={np.mean(hq):.2f}')
    ax2.set_xlabel('Hazard Quotient')
    ax2.set_ylabel('Density')
    ax2.set_title('Health Risk Distribution (Year 5)', fontsize=12, fontweight='bold')
    ax2.legend()
    
    # 3. Compartment comparison
    ax3 = fig.add_subplot(gs[1, 0])
    comps = ['sediment', 'topsoil', 'subsoil']
    means = [np.mean(results[c][-1, :]) for c in comps]
    stds = [np.std(results[c][-1, :]) for c in comps]
    ax3.bar(comps, means, yerr=stds, capsize=5, color=['brown', 'green', 'olive'], edgecolor='black')
    ax3.set_ylabel('Mercury (mg/kg)')
    ax3.set_title('Compartment Concentrations', fontsize=12, fontweight='bold')
    
    # 4. Fish risk categories
    ax4 = fig.add_subplot(gs[1, 1])
    fish = results["methylmercury_fish"][-1, :]
    cats = ['Safe\n(<0.3)', 'Moderate\n(0.3-0.5)', 'High\n(0.5-1.0)', 'Unsafe\n(>1.0)']
    counts = [np.sum(fish < 0.3), np.sum((fish >= 0.3) & (fish < 0.5)),
              np.sum((fish >= 0.5) & (fish < 1.0)), np.sum(fish >= 1.0)]
    ax4.pie(counts, labels=cats, colors=['green', 'yellow', 'orange', 'red'],
           autopct='%1.1f%%', startangle=90)
    ax4.set_title('Fish Consumption Risk', fontsize=12, fontweight='bold')
    
    # 5. HQ over time
    ax5 = fig.add_subplot(gs[1, 2])
    time_years = time_points / 365
    hq_data = results["hazard_quotient"]
    ax5.fill_between(time_years, np.percentile(hq_data, 5, axis=1),
                    np.percentile(hq_data, 95, axis=1), alpha=0.3, color='red')
    ax5.plot(time_years, np.mean(hq_data, axis=1), 'r-', linewidth=2)
    ax5.axhline(1, color='black', linestyle='--', linewidth=2)
    ax5.set_xlabel('Time (years)')
    ax5.set_ylabel('Hazard Quotient')
    ax5.set_title('Risk Trajectory', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # 6. Summary statistics table
    ax6 = fig.add_subplot(gs[2, :])
    ax6.axis('off')
    
    # Create summary table
    table_data = [
        ['Compartment', 'Year 1', 'Year 5', 'Change', 'Threshold', 'P(Exceed)'],
        ['Water (mg/L)', f'{np.mean(results["water"][4,:]):.4f}', 
         f'{np.mean(results["water"][-1,:]):.4f}',
         f'{(np.mean(results["water"][-1,:])-np.mean(results["water"][4,:])):.4f}',
         '0.002 (EPA)', f'{probs.get("Water > EPA (0.002 mg/L)", 0):.1f}%'],
        ['Sediment (mg/kg)', f'{np.mean(results["sediment"][4,:]):.2f}',
         f'{np.mean(results["sediment"][-1,:]):.2f}',
         f'+{(np.mean(results["sediment"][-1,:])-np.mean(results["sediment"][4,:])):.2f}',
         '1.06 (PEC)', f'{probs.get("Sediment > PEC (1.06 mg/kg)", 0):.1f}%'],
        ['Topsoil (mg/kg)', f'{np.mean(results["topsoil"][4,:]):.2f}',
         f'{np.mean(results["topsoil"][-1,:]):.2f}',
         f'+{(np.mean(results["topsoil"][-1,:])-np.mean(results["topsoil"][4,:])):.2f}',
         '1.0 (Agri)', f'{probs.get("Topsoil > Agricultural (1.0 mg/kg)", 0):.1f}%'],
        ['Hazard Quotient', f'{np.mean(results["hazard_quotient"][4,:]):.2f}',
         f'{np.mean(results["hazard_quotient"][-1,:]):.2f}',
         f'{(np.mean(results["hazard_quotient"][-1,:])-np.mean(results["hazard_quotient"][4,:])):.2f}',
         '1.0', f'{probs.get("HQ > 1 (health risk)", 0):.1f}%'],
    ]
    
    table = ax6.table(cellText=table_data, loc='center', cellLoc='center',
                     colWidths=[0.18, 0.12, 0.12, 0.12, 0.15, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    
    # Color header
    for j in range(6):
        table[(0, j)].set_facecolor('lightgray')
        table[(0, j)].set_text_props(fontweight='bold')
    
    plt.suptitle('MERCURY POLLUTION RISK ASSESSMENT DASHBOARD',
                fontsize=14, fontweight='bold', y=0.98)
    plt.savefig(f"{output_dir}/04_risk_dashboard.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 04_risk_dashboard.png")


def plot_sensitivity(sens: Dict, output_dir: str):
    """Plot sensitivity tornado chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    params = list(sens.keys())[:8]
    values = list(sens.values())[:8]
    colors = ['steelblue' if v > 0 else 'coral' for v in values]
    
    ax.barh(range(len(params)), values, color=colors, edgecolor='black')
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels(params)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_xlabel('Spearman Correlation with Hazard Quotient')
    ax.set_title('Sensitivity Analysis: Key Risk Drivers', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(-1, 1)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/05_sensitivity_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 05_sensitivity_analysis.png")


def plot_summary(results: Dict, validation: Dict, probs: Dict, time_points: np.ndarray, output_dir: str, model=None):
    """Create comprehensive summary figure"""
    from mercury_package.models.empirical_model import EmpiricalMercuryModel
    
    fig = plt.figure(figsize=(18, 14))
    gs = GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)
    
    time_years = time_points / 365
    if model is None:
        model = EmpiricalMercuryModel()
    time_dense = np.linspace(0, max(time_points), 200)
    
    # Row 1: Validation plots
    for i, (comp, ylabel, color) in enumerate([
        ("water", "mg/L", "blue"), ("sediment", "mg/kg", "brown"),
        ("topsoil", "mg/kg", "green"), ("subsoil", "mg/kg", "olive")
    ]):
        ax = fig.add_subplot(gs[0, i])
        
        if comp == "water":
            pred = model.predict_water(time_dense)
        elif comp == "sediment":
            pred = model.predict_sediment(time_dense)
        elif comp == "topsoil":
            pred = model.predict_topsoil(time_dense)
        else:
            pred = model.predict_subsoil(time_dense)
            
        ax.plot(time_dense/365, pred, color=color, linewidth=2)
        v = validation[comp]
        ax.scatter(np.array(v['times'])/365, v['observed'], s=80, c='red', zorder=5)
        ax.set_xlabel('Years')
        ax.set_ylabel(ylabel)
        ax.set_title(f'{comp.title()}\nR²={v["r2"]:.2f}', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    # Row 2: Monte Carlo time series
    for i, (comp, color, thresh) in enumerate([
        ("water", "blue", 0.002), ("sediment", "brown", 1.06),
        ("topsoil", "green", 1.0), ("hazard_quotient", "red", 1.0)
    ]):
        ax = fig.add_subplot(gs[1, i])
        data = results[comp]
        
        ax.fill_between(time_years, np.percentile(data, 5, axis=1),
                       np.percentile(data, 95, axis=1), alpha=0.3, color=color)
        ax.plot(time_years, np.mean(data, axis=1), color=color, linewidth=2)
        if thresh:
            ax.axhline(thresh, color='red', linestyle='--', linewidth=1)
        ax.set_xlabel('Years')
        ax.set_title(comp.replace('_', ' ').title(), fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    # Row 3: Risk summary
    ax_risk = fig.add_subplot(gs[2, :2])
    key_probs = {k: v for k, v in probs.items() if any(x in k for x in ['EPA', 'PEC', 'HQ > 1'])}
    colors = ['green' if v < 25 else 'orange' if v < 75 else 'red' for v in key_probs.values()]
    ax_risk.barh(range(len(key_probs)), list(key_probs.values()), color=colors, edgecolor='black')
    ax_risk.set_yticks(range(len(key_probs)))
    ax_risk.set_yticklabels(list(key_probs.keys()), fontsize=9)
    ax_risk.set_xlabel('Probability (%)')
    ax_risk.set_title('Key Risk Exceedance Probabilities', fontsize=12, fontweight='bold')
    ax_risk.set_xlim(0, 100)
    
    # Executive summary text
    ax_text = fig.add_subplot(gs[2, 2:])
    ax_text.axis('off')
    
    hq_mean = np.mean(results["hazard_quotient"][-1, :])
    hq_p95 = np.percentile(results["hazard_quotient"][-1, :], 95)
    risk_level = "HIGH" if hq_mean > 1 else "MODERATE" if hq_p95 > 1 else "LOW"
    
    summary_text = f"""
EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Risk Level: {risk_level}

Mercury Transport:
• Peak water concentration at ~6 months
• Rapid initial transport, then decay

Accumulation (5-year projections):
• Sediment: {np.mean(results['sediment'][-1,:]):.1f} mg/kg
• Topsoil: {np.mean(results['topsoil'][-1,:]):.1f} mg/kg

Long-term Risk:
• Mean Hazard Quotient: {hq_mean:.2f}
• P(HQ>1): {probs.get('HQ > 1 (health risk)', 0):.0f}%
• P(Sediment>PEC): {probs.get('Sediment > PEC (1.06 mg/kg)', 0):.0f}%

Key Recommendations:
• {"Immediate action required" if risk_level == "HIGH" else "Continue monitoring" if risk_level == "MODERATE" else "Maintain current practices"}
• {"Issue fish consumption advisory" if probs.get('Fish > EPA (0.3 mg/kg)', 0) > 25 else "Fish consumption acceptable"}
"""
    
    ax_text.text(0.05, 0.95, summary_text, transform=ax_text.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.suptitle('COMPREHENSIVE MERCURY POLLUTION EVALUATION',
                fontsize=16, fontweight='bold', y=0.98)
    plt.savefig(f"{output_dir}/06_comprehensive_summary.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 06_comprehensive_summary.png")
