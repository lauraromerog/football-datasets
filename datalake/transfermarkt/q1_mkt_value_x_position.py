import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set working directory to where the CSVs are
os.chdir(os.path.dirname(os.path.abspath(__file__)))

df_latest_market_value = pd.read_csv("player_latest_market_value/player_latest_market_value.csv")
df_player_profiles= pd.read_csv("player_profiles/player_profiles.csv", low_memory=False)
df_mv_hist = pd.read_csv("player_market_value/player_market_value.csv")
cols = ['player_id', 'position', 'main_position', 'foot']
df_pp = df_player_profiles[cols].copy()
df = df_latest_market_value.merge(df_pp, on='player_id', how='inner')

# EDA & CLEANING
df = df[df['value'].notna() & (df['value'] > 0)]
df = df[df['position'].notna() & (df['position']!= '')]
df = df[df['main_position'].notna() & (df['main_position']!= '')]
df = df[df['foot'].notna()& (df['foot']!= '')]
df = df[(df['main_position'] != df['position']) | (df['main_position'] == 'Goalkeeper')]
df = df[df['date_unix'].notna()]
df['value_year'] = pd.to_datetime(df['date_unix'], unit='s').dt.year.astype(int)
df['value_m'] = df['value'] / 1_000_000

# PREPARE HISTORICAL MARKET VALUE DF
df_mv_hist['value_year'] = pd.to_datetime(df_mv_hist['date_unix']).dt.year.astype(int)
df_mv_hist['value_m']    = df_mv_hist['value'] / 1_000_000

# Merge with cleaned position info (one row per player)
df_hist = df_mv_hist.merge(df[['player_id', 'position', 'main_position', 'foot']].drop_duplicates('player_id'),on='player_id', how='inner')
df_hist = df_hist[df_hist['value'].notna() & (df_hist['value'] > 0)]

# Only keep years with 100+ unique players
year_counts = df_hist.groupby('value_year')['player_id'].nunique()
valid_years = year_counts[year_counts >= 100].index


# VIZ grid:
fig = plt.figure(figsize=(16, 20))

# VIZ 1 — Distribution of market values (log scale)
ax1 = fig.add_subplot(4, 2, 1)
sns.histplot(df['value_m'], bins=80, log_scale=True, kde=True, ax=ax1)
ax1.set_title("Distribution of Player Market Values (€M, log scale)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Market Value (€M)")
ax1.set_ylabel("Count")

# VIZ 2 — Avg market value by main position
ax2 = fig.add_subplot(4, 2, 2)
main_pos_avg = (df.groupby('position')['value_m'].mean().sort_values(ascending=False).reset_index())
sns.barplot(data=main_pos_avg, x='position', y='value_m', ax=ax2)
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
ax2.set_title("Avg Market Value by Position (€M)", fontsize=12, fontweight='bold')
ax2.set_xlabel("Position")
ax2.set_ylabel("Avg Value (€M)")

# VIZ 3 — Avg market value by position group, stacked by foot
ax3 = fig.add_subplot(4, 2, 3)
foot_pos = (df.groupby(['main_position', 'foot'])['value_m'].mean().reset_index())
pivot3 = foot_pos.pivot(index='main_position', columns='foot', values='value_m').fillna(0)
pivot3 = pivot3.loc[pivot3.sum(axis=1).sort_values(ascending=False).index]
pivot3.plot(kind='bar', stacked=True, colormap='tab20', ax=ax3)
plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
ax3.set_title("Avg Market Value by Main Position, stacked by Foot (€M)", fontsize=12, fontweight='bold')
ax3.set_xlabel("Main Position")
ax3.set_ylabel("Avg Value (€M)")
ax3.legend(title="Foot", bbox_to_anchor=(1.05, 1), loc='upper left')

# VIZ 4 — Avg market value by position group + foot (grouped)
ax4 = fig.add_subplot(4, 2, 4)
pos_foot = (df.groupby(['main_position', 'foot'])['value_m'].mean().reset_index())
sns.barplot(data=pos_foot, x='main_position', y='value_m', hue='foot', palette='tab10', ax=ax4)
plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
ax4.set_title("Avg Market Value by Main Position and Foot Preference (€M)", fontsize=12, fontweight='bold')
ax4.set_xlabel("Main Position")
ax4.set_ylabel("Avg Value (€M)")
ax4.legend(title="Foot")

# VIZ 5 — Avg market value over time by main position (2015–2025)
ax5 = fig.add_subplot(4, 2, (5, 6))
time_pos = (df_hist[df_hist['value_year'].isin(valid_years) &(df_hist['value_year'] >= 2015)].groupby(['value_year', 'main_position'])['value_m'].mean().reset_index())
pivot5 = time_pos.pivot(index='value_year', columns='main_position', values='value_m')
for col in pivot5.columns:
    ax5.plot(pivot5.index, pivot5[col], marker='o', label=col)
ax5.set_xticks(pivot5.index)
plt.setp(ax5.get_xticklabels(), rotation=45, ha='right')
ax5.set_title("Avg Market Value Over Time by Main Position (€M, 2015–2025)",fontsize=12, fontweight='bold')
ax5.set_xlabel("Year")
ax5.set_ylabel("Avg Value (€M)")
ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, ncol=2)

# VIZ 6 — Pie charts: foot distribution per position group
positions = sorted(df['main_position'].unique())
pie_axes = [fig.add_subplot(4, 4, 13 + i) for i in range(4)]
for ax, pos in zip(pie_axes, positions):
    foot_counts = df[df['main_position'] == pos]['foot'].value_counts()
    ax.pie(foot_counts,labels=foot_counts.index,autopct='%1.1f%%',colors=sns.color_palette('tab10', len(foot_counts)),startangle=90)
    ax.set_title(pos, fontsize=10)

fig.text(0.5, 0.2, "Foot Preference Distribution by Position Group",ha='center', fontsize=12, fontweight='bold')

plt.suptitle("Football Player Market Value — Dashboard", fontsize=18, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig("eda_dashboard.png", bbox_inches='tight', dpi=150)