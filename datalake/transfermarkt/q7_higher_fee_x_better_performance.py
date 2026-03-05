import os

import pandas as pd
import matplotlib.pyplot as plt


os.chdir(os.path.dirname(os.path.abspath(__file__)))
df_transfers = pd.read_csv("transfer_history/transfer_history.csv")
df_team_details = pd.read_csv("team_details/team_details.csv")
df_perf = pd.read_csv("player_performances/player_performances.csv")
df_profiles = pd.read_csv("player_profiles/player_profiles.csv")

# Filter out goalkeepers
non_gk_ids = df_profiles[df_profiles['main_position'] != 'Goalkeeper']['player_id']

# Filter transfers: Big 5 buyers, valid fees
top_leagues  = ['ES1', 'GB1', 'FR1', 'L1', 'IT1']
top_team_ids = df_team_details[df_team_details['competition_id'].isin(top_leagues)]['club_id'].unique()

df_t = df_transfers[df_transfers['to_team_id'].isin(top_team_ids) & df_transfers['transfer_fee'].notna() & (df_transfers['transfer_fee'] > 0) &df_transfers['player_id'].isin(non_gk_ids)][['player_id', 'transfer_fee']].drop_duplicates()

# Aggregate performance per player across all seasons
df_p = (df_perf[df_perf['player_id'].isin(non_gk_ids)].groupby('player_id').agg(total_goals=('goals', 'sum'),total_assists=('assists', 'sum'),total_minutes=('minutes_played', 'sum')).reset_index())

# Merge
df = df_t.merge(df_p, on='player_id', how='inner')

# Quartile buckets
df['fee_quartile'] = pd.qcut(df['transfer_fee'], q=4, labels=['Q1\n(lowest)', 'Q2', 'Q3', 'Q4\n(highest)'])

# Aggregate by quartile
quartile_agg = (df.groupby('fee_quartile').agg(avg_goals=('total_goals', 'mean'),avg_assists=('total_assists', 'mean'),avg_minutes=('total_minutes', 'mean'),player_count=('player_id', 'count')).reset_index())

# Plot
metrics = ['avg_goals', 'avg_assists', 'avg_minutes']
titles = ['Avg Goals', 'Avg Assists', 'Avg Minutes Played']
colors = ['steelblue', 'darkorange', 'seagreen']

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, metric, title, color in zip(axes, metrics, titles, colors):
    ax.bar(quartile_agg['fee_quartile'], quartile_agg[metric], color=color)
    ax.set_title(title)
    ax.set_xlabel('Transfer Fee Quartile')
    ax.set_ylabel(title)

plt.suptitle("Q7: Does a Higher Transfer Fee = Better Performance?\n(Big 5 Leagues, Non-GK only)",fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig("q7_fee_vs_performance.png", bbox_inches='tight')