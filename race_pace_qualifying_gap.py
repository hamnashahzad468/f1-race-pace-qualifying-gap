import fastf1
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Setup cache
os.makedirs('f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('f1_cache')

# 2026 races that actually took place before Austria
races = [
    'Australia',
    'China',
    'Japan',
    'Miami',
    'Canada',
    'Monaco',
    'Spain',
    'Austria'
]

print("Loading race data... this may take a few minutes on first run")

all_results = []

for race in races:
    try:
        session = fastf1.get_session(2026, race, 'R')
        session.load(telemetry=False, weather=False, messages=False)
        results = session.results[['DriverNumber', 'Abbreviation',
                                   'GridPosition', 'Position']].copy()
        results['Race'] = race
        results['GridPosition'] = pd.to_numeric(results['GridPosition'],
                                                 errors='coerce')
        results['Position'] = pd.to_numeric(results['Position'],
                                             errors='coerce')
        results['PositionGain'] = results['GridPosition'] - results['Position']
        all_results.append(results)
        print(f"Loaded {race}")
    except Exception as e:
        print(f"Skipped {race}: {e}")

# Combine all results
df = pd.concat(all_results, ignore_index=True)
df = df.dropna(subset=['GridPosition', 'Position'])

# Aggregate by driver
driver_summary = df.groupby('Abbreviation').agg(
    avg_grid=('GridPosition', 'mean'),
    avg_finish=('Position', 'mean'),
    avg_gain=('PositionGain', 'mean'),
    races=('Race', 'count')
).reset_index()

driver_summary = driver_summary[driver_summary['races'] >= 3]
driver_summary = driver_summary.sort_values('avg_finish')

# --- Plotting ---
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.suptitle('Race Pace vs Qualifying Gap Model — 2026 F1 Season',
             fontsize=14, fontweight='bold')

# --- Plot 1: Avg Qualifying vs Avg Finishing Position ---
ax1 = axes[0]
scatter = ax1.scatter(driver_summary['avg_grid'],
                      driver_summary['avg_finish'],
                      c=driver_summary['avg_gain'],
                      cmap='RdYlGn', s=150, zorder=5,
                      vmin=-5, vmax=5)

for _, row in driver_summary.iterrows():
    ax1.annotate(row['Abbreviation'],
                 (row['avg_grid'], row['avg_finish']),
                 textcoords='offset points', xytext=(6, 4),
                 fontsize=8, color='white')

max_pos = 20
ax1.plot([1, max_pos], [1, max_pos], color='grey',
         linestyle='--', linewidth=1, alpha=0.5, label='Grid = Finish line')
ax1.set_xlabel('Average Qualifying Position', fontsize=11)
ax1.set_ylabel('Average Finishing Position', fontsize=11)
ax1.set_title('Qualifying Position vs Race Finishing Position\n(Below diagonal = better than grid position)', fontsize=10)
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax1, label='Avg positions gained (green = gained)')

# --- Plot 2: Positions gained/lost per driver ---
ax2 = axes[1]
colors2 = ['#00AA44' if g > 0 else '#FF3333'
           for g in driver_summary['avg_gain']]
bars = ax2.barh(driver_summary['Abbreviation'],
                driver_summary['avg_gain'],
                color=colors2, edgecolor='none', height=0.6)
ax2.axvline(x=0, color='white', linewidth=1.5)
ax2.set_xlabel('Average Positions Gained in Race', fontsize=11)
ax2.set_title('Average Positions Gained/Lost\nQualifying → Race Finish', fontsize=10)
ax2.grid(True, alpha=0.3, axis='x')

for bar, val in zip(bars, driver_summary['avg_gain']):
    ax2.text(val + (0.1 if val >= 0 else -0.1),
             bar.get_y() + bar.get_height() / 2,
             f'{val:+.1f}', va='center',
             ha='left' if val >= 0 else 'right',
             fontsize=8, color='white')

plt.tight_layout()
plt.savefig('race_pace_qualifying_gap.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nTop 5 drivers by average finishing position:")
print(driver_summary[['Abbreviation', 'avg_grid',
                        'avg_finish', 'avg_gain',
                        'races']].head().to_string(index=False))
