import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re

# Set plot style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100

# Load the cleaned dataset
file_name = "ICRISAT_District_Level_Data_Cleaned.csv"
df = pd.read_csv(file_name)

# --- Robust column resolution ---
# Some cleaned datasets may have slight naming variations (double underscores,
# repeated segments like 'production_production' or 'area_area'). To keep the
# rest of the script unchanged, map expected column names used below to actual
# dataframe columns when possible, and create safe fallbacks when not found.
def _normalize_col_name(name: str) -> str:
    n = str(name).lower().strip()
    # collapse duplicate segments that sometimes appear from earlier cleaning
    n = n.replace('production_production', 'production')
    n = n.replace('area_area', 'area')
    n = n.replace('yield_yield', 'yield')
    # collapse multiple underscores and spaces
    n = n.replace('__', '_')
    n = re.sub(r'[^a-z0-9_]', '_', n)
    n = re.sub(r'_+', '_', n)
    return n.strip('_')

# List of expected column names that the script references below.
expected_cols = [
    'state_name', 'dist_name', 'year',
    'rice_production_production_1000tons', 'wheat_production_production_1000tons',
    'oilseeds_production_production_1000tons', 'sunflower_production_production_1000tons',
    'sugarcane_production_production_1000tons',
    'rice_area_area_1000ha', 'wheat_area_area_1000ha', 'maize_area_area_1000ha',
    'maize_production_production_1000tons',
    'pearl_millet_production_production_1000tons', 'finger_millet_production_production_1000tons',
    'kharif_sorghum_production_production_1000tons', 'rabi_sorghum_production_production_1000tons',
    'groundnut_production_production_1000tons', 'soyabean_production_production_1000tons',
    'soyabean_yield_yield_kg_per_ha', 'rice_yield_yield_kg_per_ha', 'wheat_yield_yield_kg_per_ha'
]

# Build normalized map of actual columns
actual_norm_map = {col: _normalize_col_name(col) for col in df.columns}

# Resolve expected -> actual column names
resolved = {}
created = []
for exp in expected_cols:
    exp_norm = _normalize_col_name(exp)
    match = None
    for actual, actual_norm in actual_norm_map.items():
        if actual_norm == exp_norm:
            match = actual
            break
    if match:
        resolved[exp] = match
    else:
        # No exact normalized match: attempt a looser search by prefix + suffix
        prefix = exp.split('_')[0]
        candidates = [c for c in df.columns if prefix in c and ('production' in exp and 'production' in c or 'area' in exp and 'area' in c or 'yield' in exp and 'yield' in c)]
        if candidates:
            resolved[exp] = candidates[0]
        else:
            # Create a safe fallback: production/area -> 0, yields -> NaN
            if 'production' in exp or '_area_' in exp or exp.endswith('_1000ha'):
                df[exp] = 0
            else:
                df[exp] = np.nan
            resolved[exp] = exp
            created.append(exp)

if resolved:
    print('Column resolution mapping (expected -> actual):')
    for k, v in resolved.items():
        if k != v:
            print(f"  {k} -> {v}")
    if created:
        print('Created fallback columns:', created)

# For convenience, add aliases in the dataframe so later code can use the expected names
for exp, actual in resolved.items():
    if exp != actual and exp not in df.columns:
        df[exp] = df[actual]

# --- Common helper function for State Production EDA ---
def plot_top_production(data, production_col, state_col, title, top_n, filename):
    """Groups, sums, sorts, and plots top N states for a given production column."""
    # Group by state and sum the production column over all years
    state_prod = data.groupby(state_col)[production_col].sum().sort_values(ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=state_prod.values, y=state_prod.index, palette="viridis")
    plt.xlabel(production_col.replace('_production_1000tons', '').replace('_', ' ').title() + ' (1000 tons)')
    plt.ylabel('State Name')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# --- 1. Top 7 RICE PRODUCTION State Data (Bar_plot) ---
plot_top_production(
    df,
    'rice_production_production_1000tons',
    'state_name',
    'Top 7 States for Rice Production (Total All Years)',
    7,
    'top_7_rice_production_bar.png'
)

# --- 2. Top 5 Wheat Producing States Data (Bar_chart) and its percentage(%) (Pie_chart) ---
WHEAT_PROD_COL = 'wheat_production_production_1000tons'
top_n_wheat = 5
wheat_prod_states = df.groupby('state_name')[WHEAT_PROD_COL].sum().sort_values(ascending=False).head(top_n_wheat)
total_wheat_prod = wheat_prod_states.sum()
wheat_prod_percent = (wheat_prod_states / total_wheat_prod) * 100

# Bar Chart
plt.figure(figsize=(10, 6))
sns.barplot(x=wheat_prod_states.values, y=wheat_prod_states.index, palette="Reds_r")
plt.xlabel('Wheat Production (1000 tons)')
plt.ylabel('State Name')
plt.title(f'Top {top_n_wheat} States for Wheat Production (Total All Years)')
plt.tight_layout()
plt.savefig('top_5_wheat_production_bar.png')
plt.close()

# Pie Chart
plt.figure(figsize=(8, 8))
plt.pie(
    wheat_prod_percent,
    labels=[f'{state} ({p:.1f}%)' for state, p in wheat_prod_percent.items()],
    autopct='',
    startangle=90,
    wedgeprops={'edgecolor': 'black'},
    colors=sns.color_palette("Reds_r", top_n_wheat)
)
plt.title(f'Percentage Share of Top {top_n_wheat} States in Total Wheat Production (of Top 5)')
plt.tight_layout()
plt.savefig('top_5_wheat_production_pie.png')
plt.close()

# --- 3. Oil seed production by top 5 states / 13. Oilseed Production in Major States ---
plot_top_production(
    df,
    'oilseeds_production_production_1000tons',
    'state_name',
    'Top 5 States for Oilseeds Production (Total All Years)',
    5,
    'top_5_oilseeds_production_bar.png'
)

# --- 4. Top 7 SUNFLOWER PRODUCTION State ---
plot_top_production(
    df,
    'sunflower_production_production_1000tons',
    'state_name',
    'Top 7 States for Sunflower Production (Total All Years)',
    7,
    'top_7_sunflower_production_bar.png'
)

# --- 5. India's SUGARCANE PRODUCTION From Last 50 Years (Line_plot) ---
sugarcane_trend = df.groupby('year')['sugarcane_production_production_1000tons'].sum().reset_index()

plt.figure(figsize=(12, 6))
sns.lineplot(data=sugarcane_trend, x='year', y='sugarcane_production_production_1000tons', marker='o', color='forestgreen')
plt.xlabel('Year')
plt.ylabel('Sugarcane Production (1000 tons)')
plt.title("India's Sugarcane Production Over Time (1966-2015)")
plt.xticks(sugarcane_trend['year'][::5])
plt.grid(True)
plt.tight_layout()
plt.savefig('sugarcane_production_trend_line.png')
plt.close()

# --- 6. Rice Production Vs Wheat Production (Last 50y) ---
national_prod_trend = df.groupby('year').agg({
    'rice_production_production_1000tons': 'sum',
    'wheat_production_production_1000tons': 'sum'
}).reset_index()

plt.figure(figsize=(12, 6))
sns.lineplot(data=national_prod_trend, x='year', y='rice_production_production_1000tons', label='Rice Production', marker='o', color='blue')
sns.lineplot(data=national_prod_trend, x='year', y='wheat_production_production_1000tons', label='Wheat Production', marker='o', color='red')
plt.xlabel('Year')
plt.ylabel('Production (1000 tons)')
plt.title('Rice Production Vs Wheat Production Over Time (1966-2015)')
plt.xticks(national_prod_trend['year'][::5])
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('rice_vs_wheat_production_trend_line.png')
plt.close()

# --- 7. Rice Production By West Bengal Districts ---
west_bengal_df = df[df['state_name'] == 'West Bengal']
wb_district_prod = west_bengal_df.groupby('dist_name')['rice_production_production_1000tons'].sum().sort_values(ascending=False)

plt.figure(figsize=(10, 8))
sns.barplot(x=wb_district_prod.values, y=wb_district_prod.index, palette="Blues_r")
plt.xlabel('Rice Production (1000 tons)')
plt.ylabel('District Name')
plt.title('Rice Production by West Bengal Districts (Total All Years)')
plt.tight_layout()
plt.savefig('west_bengal_rice_production_districts_bar.png')
plt.close()

# --- 8. Top 10 Wheat Production Years From UP ---
up_df = df[df['state_name'] == 'Uttar Pradesh']
up_yearly_wheat = up_df.groupby('year')['wheat_production_production_1000tons'].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 6))
sns.barplot(x=up_yearly_wheat.index.astype(str), y=up_yearly_wheat.values, palette="Oranges_r")
plt.xlabel('Year')
plt.ylabel('Wheat Production (1000 tons)')
plt.title('Top 10 Wheat Production Years in Uttar Pradesh')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('top_10_up_wheat_production_years_bar.png')
plt.close()

# --- 9. Millet Production (Last 50y) ---
df['total_millet_production'] = df['pearl_millet_production_production_1000tons'] + df['finger_millet_production_production_1000tons']
millet_trend = df.groupby('year')['total_millet_production'].sum().reset_index()

plt.figure(figsize=(12, 6))
sns.lineplot(data=millet_trend, x='year', y='total_millet_production', marker='o', color='purple')
plt.xlabel('Year')
plt.ylabel('Millet Production (1000 tons)')
plt.title('India\'s Total Millet Production Over Time (1966-2015)')
plt.xticks(millet_trend['year'][::5])
plt.grid(True)
plt.tight_layout()
plt.savefig('millet_production_trend_line.png')
plt.close()

# --- 10. Sorghum Production (Kharif and Rabi) by Region ---
sorghum_prod = df.groupby('state_name').agg({
    'kharif_sorghum_production_production_1000tons': 'sum',
    'rabi_sorghum_production_production_1000tons': 'sum'
})
sorghum_prod['total_sorghum'] = sorghum_prod.sum(axis=1)
sorghum_prod_top = sorghum_prod.sort_values(by='total_sorghum', ascending=False).head(10).drop(columns=['total_sorghum'])

sorghum_prod_top_melt = sorghum_prod_top.reset_index().melt(
    id_vars='state_name',
    var_name='Sorghum Type',
    value_name='Production'
).replace({
    'kharif_sorghum_production_production_1000tons': 'Kharif Sorghum',
    'rabi_sorghum_production_production_1000tons': 'Rabi Sorghum'
})

plt.figure(figsize=(12, 7))
sns.barplot(
    data=sorghum_prod_top_melt,
    x='Production',
    y='state_name',
    hue='Sorghum Type',
    palette={'Kharif Sorghum': 'orange', 'Rabi Sorghum': 'brown'}
)
plt.xlabel('Production (1000 tons)')
plt.ylabel('State Name')
plt.title('Kharif and Rabi Sorghum Production by Top 10 States (Total All Years)')
plt.legend(title='Sorghum Type')
plt.tight_layout()
plt.savefig('sorghum_production_kharif_rabi_stacked_bar.png')
plt.close()

# --- 11. Top 7 States for Groundnut Production ---
plot_top_production(
    df,
    'groundnut_production_production_1000tons',
    'state_name',
    'Top 7 States for Groundnut Production (Total All Years)',
    7,
    'top_7_groundnut_production_bar.png'
)

# --- 12. Soybean Production by Top 5 States and Yield Efficiency ---
SOYBEAN_PROD_COL = 'soyabean_production_production_1000tons'
SOYBEAN_YIELD_COL = 'soyabean_yield_yield_kg_per_ha'

# Calculate state aggregates: total production and average yield
soybean_states = df.groupby('state_name').agg(
    total_production=(SOYBEAN_PROD_COL, 'sum'),
    average_yield=(SOYBEAN_YIELD_COL, 'mean')
).sort_values(by='total_production', ascending=False).head(5)

# Production Bar Chart
plt.figure(figsize=(10, 6))
sns.barplot(x=soybean_states.index, y=soybean_states['total_production'], palette="Greens_r")
plt.xlabel('State Name')
plt.ylabel('Soybean Production (1000 tons)')
plt.title('Top 5 States for Soybean Production (Total All Years)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('top_5_soybean_production_bar.png')
plt.close()

# Yield Efficiency Bar Chart
plt.figure(figsize=(10, 6))
sns.barplot(x=soybean_states.index, y=soybean_states['average_yield'].sort_values(ascending=False), palette="Blues_r")
plt.xlabel('State Name')
plt.ylabel('Average Soybean Yield (Kg per ha)')
plt.title('Soybean Yield Efficiency by Top 5 Producing States (Average All Years)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('top_5_soybean_yield_efficiency_bar.png')
plt.close()

# --- 14. Impact of Area Cultivated on Production (Rice, Wheat, Maize) ---
area_prod_df = df.groupby('year').agg({
    'rice_area_area_1000ha': 'sum',
    'rice_production_production_1000tons': 'sum',
    'wheat_area_area_1000ha': 'sum',
    'wheat_production_production_1000tons': 'sum',
    'maize_area_area_1000ha': 'sum',
    'maize_production_production_1000tons': 'sum'
}).reset_index()

# Scatter Plot for Area vs. Production (National Totals)
plt.figure(figsize=(15, 5))

# Rice
plt.subplot(1, 3, 1)
sns.regplot(data=area_prod_df, x='rice_area_area_1000ha', y='rice_production_production_1000tons', scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
plt.title('Rice: Area vs. Production')
plt.xlabel('Area Cultivated (1000 ha)')
plt.ylabel('Production (1000 tons)')

# Wheat
plt.subplot(1, 3, 2)
sns.regplot(data=area_prod_df, x='wheat_area_area_1000ha', y='wheat_production_production_1000tons', scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
plt.title('Wheat: Area vs. Production')
plt.xlabel('Area Cultivated (1000 ha)')

# Maize
plt.subplot(1, 3, 3)
sns.regplot(data=area_prod_df, x='maize_area_area_1000ha', y='maize_production_production_1000tons', scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
plt.title('Maize: Area vs. Production')
plt.xlabel('Area Cultivated (1000 ha)')

plt.suptitle('Impact of Area Cultivated on Production (National Totals Over Time)', fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('area_vs_production_scatter.png')
plt.close()

# --- 15. Rice vs. Wheat Yield Across States ---
state_yields = df.groupby('state_name').agg(
    rice_yield=('rice_yield_yield_kg_per_ha', 'mean'),
    wheat_yield=('wheat_yield_yield_kg_per_ha', 'mean')
).dropna()

plt.figure(figsize=(10, 8))
sns.scatterplot(data=state_yields, x='rice_yield', y='wheat_yield', hue=state_yields.index, legend=False, s=100)

for i in range(len(state_yields)):
    if (state_yields['rice_yield'].iloc[i] > state_yields['rice_yield'].quantile(0.75)) or \
       (state_yields['wheat_yield'].iloc[i] > state_yields['wheat_yield'].quantile(0.75)):
        plt.text(state_yields['rice_yield'].iloc[i] * 1.02, state_yields['wheat_yield'].iloc[i],
                 state_yields.index[i], fontsize=8)

plt.xlabel('Average Rice Yield (Kg per ha)')
plt.ylabel('Average Wheat Yield (Kg per ha)')
plt.title('Rice vs. Wheat Yield Across States (Average All Years)')
plt.tight_layout()
plt.savefig('rice_vs_wheat_yield_scatter.png')
plt.close()