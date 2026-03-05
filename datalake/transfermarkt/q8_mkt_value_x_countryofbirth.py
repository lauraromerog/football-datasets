import os
import pandas as pd
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))
df_transfers = pd.read_csv("transfer_history/transfer_history.csv")
df_profiles  = pd.read_csv("player_profiles/player_profiles.csv")

# Filter out goalkeepers and nulls
df_profiles_clean = df_profiles[(df_profiles['main_position'] != 'Goalkeeper') &(df_profiles['country_of_birth'].notna())]

# Top 20 countries of birth by player count
top_countries = (df_profiles_clean['country_of_birth'].value_counts().head(20).index.tolist())

# Clean transfers
df_t = df_transfers[df_transfers['transfer_fee'].notna()      & (df_transfers['transfer_fee'] > 0) & df_transfers['value_at_transfer'].notna() & (df_transfers['value_at_transfer'] > 0)].copy()

# Compute premium ratio
df_t['premium_ratio'] = df_t['transfer_fee'] / df_t['value_at_transfer']

# Merge with profiles
df = df_t.merge(df_profiles_clean[['player_id', 'country_of_birth']], on='player_id', how='inner')

# Keep only top 20 countries
df = df[df['country_of_birth'].isin(top_countries)]

# Order countries by median premium ratio for clean visual
country_order = (df.groupby('country_of_birth')['premium_ratio'].median().sort_values(ascending=True).index.tolist())

# Plot — box plot shows distribution nicely
fig, ax = plt.subplots(figsize=(12, 8))

data_grouped = [df[df['country_of_birth'] == c]['premium_ratio'].values for c in country_order]
ax.boxplot(data_grouped, vert=False, labels=country_order, patch_artist=True, boxprops=dict(facecolor='steelblue', alpha=0.6), medianprops=dict(color='red', linewidth=2),flierprops=dict(marker='o', markersize=3, alpha=0.3))
ax.axvline(x=1, color='gray', linestyle='--', linewidth=1, label='Ratio = 1 (fee equals value)')
ax.set_xlabel('Transfer Fee / Market Value at Transfer')
ax.set_title('Market Value Premium by Country of Birth\n(Top 20 Countries, Non-GK, Big 5 excluded GK)',fontsize=13, fontweight='bold')
ax.legend()
plt.tight_layout()
ax.set_xlim(0, 5)
ax.set_xlabel('Transfer Fee / Market Value at Transfer (capped at 5x)')
plt.savefig("q8_nationality_premium.png", bbox_inches='tight')