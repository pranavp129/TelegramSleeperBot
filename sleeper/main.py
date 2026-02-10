from config.settings import OSU_DYNASTY_LEAGUE_ID
from sleeper.client import SleeperClient
from sleeper.trades import find_player_trades

client = SleeperClient(OSU_DYNASTY_LEAGUE_ID)

PLAYER_ID = "8146" # garrett wilson to test
all_trades = []

for week in range(1, 19):
    txns = client.get_transactions(week)
    player_trades = find_player_trades(txns, PLAYER_ID, week)
    all_trades.extend(player_trades)

print(f"Found {len(all_trades)} trades")
