import pandas as pd
import numpy as np  
import matplotlib.pyplot as plt
import seaborn as sns
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#Q2: Transfer Market Inflation
# Prepare df with avg fee and value by season
df_transfers   = pd.read_csv("transfer_history/transfer_history.csv")
df_market_hist = pd.read_csv("player_market_value/player_market_value.csv")
df_market_hist['season'] = pd.to_datetime(df_market_hist['date_unix'], errors='coerce').dt.year
df_market_hist = df_market_hist[df_market_hist['season'].notna()]
df_market_hist['season'] = df_market_hist['season'].astype(int)
#Prep transfer fees by season
df_fees = df_transfers[df_transfers['transfer_fee'].notna() & (df_transfers['transfer_fee'] > 0)]
fee_by_season = (df_fees.groupby('season_name')['transfer_fee'].mean().reset_index().rename(columns={'season_name': 'season', 'transfer_fee': 'avg_fee_m'}))
fee_by_season['avg_fee_m'] = fee_by_season['avg_fee_m'] / 1_000_000
#Prep market values by season
df_mv = df_market_hist[df_market_hist['value'].notna() & (df_market_hist['value'] > 0)]
value_by_season = (df_mv.groupby('season')['value'].mean().reset_index().rename(columns={'value': 'avg_value_m'}))
value_by_season['avg_value_m'] = value_by_season['avg_value_m'] / 1_000_000
value_by_season['season'] = value_by_season['season'].astype(str)
# Convert "00/01" → 2000, "15/16" → 2015, etc
def season_to_year(s):
    start = int(str(s).split('/')[0])
    return start + 2000 if start < 50 else start + 1900
fee_by_season['season_year'] = fee_by_season['season'].apply(season_to_year).astype(int)
fee_by_season['season_year'] = fee_by_season['season_year'].astype(int)
value_by_season['season'] = value_by_season['season'].astype(int)
#Merge on the converted year
df_inflation = fee_by_season.merge(value_by_season, left_on='season_year', right_on='season', how='inner').dropna()
# Filter to meaningful range
df_inflation = df_inflation[df_inflation['season_year'].between(2004, 2025)].sort_values('season_year')
# % premium: how much more clubs pay vs market value
df_inflation['fee_premium_pct'] = ((df_inflation['avg_fee_m'] - df_inflation['avg_value_m']) /df_inflation['avg_value_m'] * 100).round(1)
df_inflation['fee_idx'] = df_inflation['avg_fee_m']/df_inflation['avg_fee_m'].iloc[0]* 100
df_inflation['value_idx'] = df_inflation['avg_value_m'] / df_inflation['avg_value_m'].iloc[0] * 100
# PLOTS
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
# PLOT 1: raw values
axes[0].plot(df_inflation['season_year'], df_inflation['avg_fee_m'], marker='o', label='Avg Transfer Fee (€M)')
axes[0].plot(df_inflation['season_year'], df_inflation['avg_value_m'], marker='s', label='Avg Market Value (€M)')
# Trend lines
for col, color in [('avg_fee_m', 'steelblue'), ('avg_value_m', 'darkorange')]:
    z = np.polyfit(df_inflation['season_year'], df_inflation[col], 1)
    p = np.poly1d(z)
    axes[0].plot(df_inflation['season_year'], p(df_inflation['season_year']),'--', color=color, alpha=0.5, linewidth=1.5)
axes[0].set_title("Avg Transfer Fee vs Market Value by Season")
axes[0].set_xlabel("Season")
axes[0].set_ylabel("€M")
axes[0].legend()
plt.setp(axes[0].get_xticklabels(), rotation=45, ha='right')
# PLOT 2: indexed growth + trend lines + annotations
axes[1].plot(df_inflation['season_year'], df_inflation['fee_idx'],   marker='o', label='Fee Growth Index')
axes[1].plot(df_inflation['season_year'], df_inflation['value_idx'], marker='s', label='Market Value Growth Index')
# Trend lines
for col, color in [('fee_idx', 'steelblue'), ('value_idx', 'darkorange')]:
    z = np.polyfit(df_inflation['season_year'], df_inflation[col], 1)
    p = np.poly1d(z)
    axes[1].plot(df_inflation['season_year'], p(df_inflation['season_year']),'--', color=color, alpha=0.5, linewidth=1.5)
axes[1].set_title("Indexed Growth: Fees vs Market Values (Base=100)")
axes[1].set_xlabel("Season")
axes[1].set_ylabel("Index (Base=100)")
axes[1].legend()
plt.setp(axes[1].get_xticklabels(), rotation=45, ha='right')
plt.suptitle("Q2: Transfer Market Inflation", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("q2_transfer_inflation.png")