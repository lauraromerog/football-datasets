#scouting efficiency
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


os.chdir(os.path.dirname(os.path.abspath(__file__)))
df_transfers    = pd.read_csv("transfer_history/transfer_history.csv")
df_team_details = pd.read_csv("team_details/team_details.csv")

# Filter to Big 5 leagues
top_leagues  = ['ES1', 'GB1', 'FR1', 'L1', 'IT1']
df_top_teams = (df_team_details[df_team_details['competition_id'].isin(top_leagues)][['club_id', 'club_name', 'competition_id']].drop_duplicates())
top_team_ids = df_top_teams['club_id'].tolist()

# Clean transfers
df_fees = df_transfers[df_transfers['transfer_fee'].notna() & (df_transfers['transfer_fee'] > 0) & df_transfers['value_at_transfer'].notna()  & (df_transfers['value_at_transfer'] > 0)].copy()

# Keep transfers where both teams are in Big 5
df_fees = df_transfers[df_transfers['transfer_fee'].notna()& (df_transfers['transfer_fee'] > 0) & df_transfers['value_at_transfer'].notna() & (df_transfers['value_at_transfer'] > 0)].copy()

# Add league for buying club
df_fees = df_fees.merge(df_top_teams.rename(columns={'club_id': 'to_team_id', 'competition_id': 'buy_league'})[['to_team_id', 'buy_league']],on='to_team_id', how='left')

# Add league for selling club
df_fees = df_fees.merge(df_top_teams.rename(columns={'club_id': 'from_team_id', 'competition_id': 'sell_league'})[['from_team_id', 'sell_league']],on='from_team_id', how='left')

# % overpay
df_fees['overpay_pct'] = ((df_fees['transfer_fee'] - df_fees['value_at_transfer']) / df_fees['value_at_transfer'] * 100)

df_buy  = df_fees[df_fees['to_team_id'].isin(top_team_ids)]
df_sell = df_fees[df_fees['from_team_id'].isin(top_team_ids)]
# Min threshold
MIN_TRANSFERS = 10
valid_buyers  = df_fees['to_team_id'].value_counts()
valid_buyers  = valid_buyers[valid_buyers >= MIN_TRANSFERS].index
valid_sellers = df_fees['from_team_id'].value_counts()
valid_sellers = valid_sellers[valid_sellers >= MIN_TRANSFERS].index
df_buy  = df_fees[df_fees['to_team_id'].isin(valid_buyers)]
df_sell = df_fees[df_fees['from_team_id'].isin(valid_sellers)] 

# Aggregations
buy_eff = (
    df_buy.groupby(['to_team_name', 'buy_league'])
    .agg(transfers_in=('player_id', 'count'), avg_buy_overpay_pct=('overpay_pct', 'mean'))
    .reset_index()
    .query('avg_buy_overpay_pct < 0')
)
buy_eff['avg_buy_discount_pct'] = buy_eff['avg_buy_overpay_pct'].abs()
top_buyers = buy_eff.nlargest(15, 'avg_buy_discount_pct')

sell_eff = (
    df_sell.groupby(['from_team_name', 'sell_league'])
    .agg(transfers_out=('player_id', 'count'), avg_sell_premium_pct=('overpay_pct', 'mean'))
    .reset_index()
)
sell_eff = sell_eff[sell_eff['avg_sell_premium_pct'] > 0].nlargest(15, 'avg_sell_premium_pct')

# Plot
league_colors = {'ES1': 'red', 'GB1': 'purple', 'FR1': 'blue', 'L1': 'gold', 'IT1': 'green'}

fig, axes = plt.subplots(2, 1, figsize=(10, 14))

axes[0].barh(top_buyers['to_team_name'], top_buyers['avg_buy_discount_pct'],color=[league_colors.get(l, 'gray') for l in top_buyers['buy_league']])
axes[0].set_title("Top 15 Clubs: Buying Below Market Value (%)")
axes[0].set_xlabel("% below market value")

axes[1].barh(sell_eff['from_team_name'], sell_eff['avg_sell_premium_pct'], color=[league_colors.get(l, 'gray') for l in sell_eff['sell_league']])
axes[1].set_title("Top 15 Clubs: Selling Above Market Value (%)")
axes[1].set_xlabel("% above market value")

legend_elements = [Patch(facecolor=c, label=l) for l, c in league_colors.items()]
fig.legend(handles=legend_elements, title='League', loc='lower center',ncol=5, bbox_to_anchor=(0.5, -0.05))

plt.suptitle("Q3: Scouting Efficiency — Big 5 Leagues Only", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("q3_scouting_efficiency.png", bbox_inches='tight')