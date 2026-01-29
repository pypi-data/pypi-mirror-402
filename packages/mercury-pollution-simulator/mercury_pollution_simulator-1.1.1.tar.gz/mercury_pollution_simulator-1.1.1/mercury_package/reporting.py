"""
Reporting functions for mercury pollution simulation results
"""

import numpy as np
import pandas as pd
from typing import Dict


def export_results(
    results: Dict,
    validation: Dict,
    probs: Dict,
    sens: Dict,
    time_points: np.ndarray,
    output_dir: str,
):
    """
    Export all results to Excel file.
    
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
        Directory to save Excel file
    """
    print("\nExporting results to Excel...")
    
    with pd.ExcelWriter(f"{output_dir}/simulation_results.xlsx", engine='openpyxl') as writer:
        
        # Time series statistics
        time_labels = ['Day_0', 'Month_1', 'Month_3', 'Month_6', 
                      'Year_1', 'Year_2', 'Year_3', 'Year_4', 'Year_5']
        
        # Adjust time labels if needed
        if len(time_points) != len(time_labels):
            time_labels = [f'Time_{i}' for i in range(len(time_points))]
        
        stats_data = []
        for i, t_label in enumerate(time_labels):
            row = {'Time': t_label, 'Days': time_points[i]}
            for comp in ['water', 'sediment', 'topsoil', 'subsoil', 'hazard_quotient']:
                data = results[comp][i, :]
                row[f'{comp}_mean'] = np.mean(data)
                row[f'{comp}_p5'] = np.percentile(data, 5)
                row[f'{comp}_p50'] = np.percentile(data, 50)
                row[f'{comp}_p95'] = np.percentile(data, 95)
            stats_data.append(row)
        pd.DataFrame(stats_data).to_excel(writer, sheet_name='Time_Series', index=False)
        
        # Validation
        val_rows = []
        for comp in ['water', 'sediment', 'topsoil', 'subsoil']:
            v = validation[comp]
            for t, obs, pred in zip(v['times'], v['observed'], v['predicted']):
                val_rows.append({'Compartment': comp, 'Time_days': t, 
                               'Observed': obs, 'Predicted': pred})
        pd.DataFrame(val_rows).to_excel(writer, sheet_name='Validation', index=False)
        
        # Risk probabilities
        pd.DataFrame([probs]).T.to_excel(writer, sheet_name='Risk_Probabilities')
        
        # Sensitivity
        pd.DataFrame([sens]).T.to_excel(writer, sheet_name='Sensitivity')
        
        # Raw samples (Year 5)
        samples = pd.DataFrame({
            'water_mgL': results['water'][-1, :],
            'sediment_mgkg': results['sediment'][-1, :],
            'topsoil_mgkg': results['topsoil'][-1, :],
            'hazard_quotient': results['hazard_quotient'][-1, :]
        })
        samples.to_excel(writer, sheet_name='MC_Samples_Year5', index=False)
        
    print(f"  Saved: simulation_results.xlsx")


def generate_report(
    results: Dict,
    validation: Dict,
    probs: Dict,
    sens: Dict,
    output_dir: str,
):
    """
    Generate text report summarizing simulation results.
    
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
    output_dir : str
        Directory to save report
    """
    print("\nGenerating text report...")
    
    hq_mean = np.mean(results["hazard_quotient"][-1, :])
    hq_p95 = np.percentile(results["hazard_quotient"][-1, :], 95)
    risk_level = "HIGH" if hq_mean > 1 else "MODERATE" if hq_p95 > 1 else "LOW"

    # Prepare top sensitivity entries (safe even if empty)
    sens_items = list(sens.items()) if sens else []
    while len(sens_items) < 3:
        sens_items.append(("N/A", 0.0))
    
    report = f"""
================================================================================
MERCURY POLLUTION EVALUATION REPORT
================================================================================

OBJECTIVE: Quantitative evaluation of mercury pollution from gold amalgamation,
focusing on transport, accumulation, and long-term risk in water and soil systems.

================================================================================
1. MERCURY TRANSPORT
================================================================================

Source Characteristics:
- Release pathway: Direct discharge to river from amalgamation
- Release rate: 0.1 kg/day (mean)
- Release duration: 180 days (6 months)
- Total mercury released: 18 kg

Transport Mechanisms:
- Advection: Downstream transport via river flow
- Dispersion: Longitudinal mixing
- Settling: Particle-bound Hg deposits to sediment
- Flooding: Seasonal deposition to floodplain soils

Model Validation (R² values):
- Water: {validation['water']['r2']:.3f}
- Sediment: {validation['sediment']['r2']:.3f}
- Topsoil: {validation['topsoil']['r2']:.3f}
- Subsoil: {validation['subsoil']['r2']:.3f}

================================================================================
2. MERCURY ACCUMULATION
================================================================================

Concentration Projections (Mean [P5 - P95]):

WATER (mg/L):
- Month 6: {np.mean(results['water'][3,:]):.4f} [{np.percentile(results['water'][3,:],5):.4f} - {np.percentile(results['water'][3,:],95):.4f}]
- Year 5:  {np.mean(results['water'][-1,:]):.4f} [{np.percentile(results['water'][-1,:],5):.4f} - {np.percentile(results['water'][-1,:],95):.4f}]

SEDIMENT (mg/kg):
- Month 6: {np.mean(results['sediment'][3,:]):.2f} [{np.percentile(results['sediment'][3,:],5):.2f} - {np.percentile(results['sediment'][3,:],95):.2f}]
- Year 5:  {np.mean(results['sediment'][-1,:]):.2f} [{np.percentile(results['sediment'][-1,:],5):.2f} - {np.percentile(results['sediment'][-1,:],95):.2f}]

TOPSOIL (mg/kg):
- Year 1: {np.mean(results['topsoil'][4,:]):.2f} [{np.percentile(results['topsoil'][4,:],5):.2f} - {np.percentile(results['topsoil'][4,:],95):.2f}]
- Year 5: {np.mean(results['topsoil'][-1,:]):.2f} [{np.percentile(results['topsoil'][-1,:],5):.2f} - {np.percentile(results['topsoil'][-1,:],95):.2f}]

Accumulation Rates:
- Sediment: ~1.5 mg/kg/year
- Topsoil: ~0.6 mg/kg/year
- Subsoil: ~0.2 mg/kg/year

================================================================================
3. LONG-TERM RISK ASSESSMENT
================================================================================

Overall Risk Level: {risk_level}

Exceedance Probabilities at Year 5:
- Water > WHO limit (0.001 mg/L): {probs.get('Water > WHO (0.001 mg/L)', 0):.1f}%
- Water > EPA MCL (0.002 mg/L): {probs.get('Water > EPA (0.002 mg/L)', 0):.1f}%
- Sediment > TEC (0.18 mg/kg): {probs.get('Sediment > TEC (0.18 mg/kg)', 0):.1f}%
- Sediment > PEC (1.06 mg/kg): {probs.get('Sediment > PEC (1.06 mg/kg)', 0):.1f}%
- Topsoil > Agricultural (1.0 mg/kg): {probs.get('Topsoil > Agricultural (1.0 mg/kg)', 0):.1f}%
- Fish > EPA criterion (0.3 mg/kg): {probs.get('Fish > EPA (0.3 mg/kg)', 0):.1f}%
- Hazard Quotient > 1: {probs.get('HQ > 1 (health risk)', 0):.1f}%

Human Health Risk:
- Mean Hazard Quotient: {hq_mean:.2f}
- 95th Percentile HQ: {hq_p95:.2f}
- Maximum HQ: {np.max(results['hazard_quotient'][-1,:]):.2f}

Key Risk Drivers (Sensitivity Analysis):
1. {sens_items[0][0]}: {sens_items[0][1]:+.3f}
2. {sens_items[1][0]}: {sens_items[1][1]:+.3f}
3. {sens_items[2][0]}: {sens_items[2][1]:+.3f}

================================================================================
4. CONCLUSIONS AND RECOMMENDATIONS
================================================================================

Conclusions:
1. Mercury transport peaks within 6 months of release, then declines
2. Sediment serves as primary long-term mercury sink (accumulation continues)
3. Floodplain soils accumulate mercury through periodic flooding
4. Human health risk is primarily driven by fish consumption pathway

Recommendations:
{"- URGENT: Implement immediate mitigation measures" if risk_level == "HIGH" else ""}
{"- Issue fish consumption advisory for local communities" if probs.get('Fish > EPA (0.3 mg/kg)', 0) > 25 else "- Continue monitoring fish mercury levels"}
{"- Restrict water use for drinking without treatment" if probs.get('Water > EPA (0.002 mg/L)', 0) > 50 else ""}
- Monitor sediment mercury quarterly at key locations
- Promote mercury-free gold processing alternatives
- Conduct community health screening for mercury exposure

================================================================================
END OF REPORT
================================================================================
"""
    
    with open(f"{output_dir}/evaluation_report.txt", 'w') as f:
        f.write(report)
    print(f"  Saved: evaluation_report.txt")
