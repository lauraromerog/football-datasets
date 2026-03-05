import os

import pandas as pd
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))

df_profiles = pd.read_csv("player_profiles/player_profiles.csv")
df_national = pd.read_csv("player_national_performances/player_national_performances.csv")
df_lmv = pd.read_csv("player_latest_market_value/player_latest_market_value.csv")
df_mv = pd.read_csv("player_market_value/player_market_value.csv")

# Active players only
df_active = df_profiles[~df_profiles['current_club_name'].isin(['Retired', '---', '0']) &df_profiles['current_club_name'].notna()][['player_id']]

# Caps — active national players only
df_caps = (df_national[(df_national['career_state'] == 'CURRENT_NATIONAL_PLAYER') &(df_national['matches'] > 0)].groupby('player_id')['matches'].sum().reset_index().rename(columns={'matches': 'total_caps'}))
df_caps = df_caps[df_caps['total_caps'] > 0]

# Market value — latest first, fallback
df_lmv_clean = df_lmv[df_lmv['value'].notna() & (df_lmv['value'] > 0)][['player_id', 'value']].rename(columns={'value': 'lmv'})
df_mv_clean = df_mv[df_mv['value'].notna() & (df_mv['value'] > 0)][['player_id', 'value']].rename(columns={'value': 'mv'})

df_values = df_lmv_clean.merge(df_mv_clean, on='player_id', how='outer')
df_values['market_value'] = df_values['lmv'].combine_first(df_values['mv'])
df_values = df_values[df_values['market_value'].notna()][['player_id', 'market_value']]

# Combine
df = (df_active.merge(df_caps,   on='player_id', how='inner').merge(df_values, on='player_id', how='inner'))

# Cap buckets
def cap_bucket(c):
    if c <= 10:  return '1–10'
    elif c <= 50: return '11–50'
    else: return '50+'

cap_order = ['1–10', '11–50', '50+']
df['cap_bucket'] = pd.Categorical(df['total_caps'].apply(cap_bucket), categories=cap_order, ordered=True)

# Aggregate
agg = (df.groupby('cap_bucket', observed=True).agg(avg_market_value=('market_value', 'mean'),median_market_value=('market_value', 'median'),player_count=('player_id', 'count')).reset_index())

# Plot
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

colors = ['#6fa3bf', '#3a7ca5', '#1b4f72']

# Bar — median market value
axes[0].bar(agg['cap_bucket'], agg['median_market_value'] / 1e6, color=colors)
axes[0].set_title('Median Market Value by International Caps')
axes[0].set_xlabel('Cap Bucket')
axes[0].set_ylabel('Median Market Value (€M)')
for i, row in agg.iterrows():
    axes[0].text(i, row['median_market_value'] / 1e6 + 0.2,f"n={row['player_count']}", ha='center', fontsize=9)

# Box plot — distribution
data_grouped = [df[df['cap_bucket'] == c]['market_value'].values / 1e6 for c in cap_order]
axes[1].boxplot(data_grouped, labels=cap_order, patch_artist=True, boxprops=dict(facecolor='steelblue', alpha=0.6), medianprops=dict(color='red', linewidth=2),flierprops=dict(marker='o', markersize=3, alpha=0.3))
axes[1].set_ylim(0, 50)
axes[1].set_title('Market Value Distribution by Cap Bucket\n(capped at €50M)')
axes[1].set_xlabel('Cap Bucket')
axes[1].set_ylabel('Market Value (€M, capped at €50M)')

plt.suptitle('Q10: Do International Caps Correlate with Market Value?', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig("q10_caps_vs_market_value.png", bbox_inches='tight')