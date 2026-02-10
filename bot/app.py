import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
from uuid import uuid4
from sleeper.client import SleeperClient
from sleeper.trades import extract_trade_details, find_trades_for_player
from sleeper.helpers import get_player_id
from config.settings import OSU_DYNASTY_LEAGUE_ID

client = SleeperClient(OSU_DYNASTY_LEAGUE_ID)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if not query:
        return

    results = [
        InlineQueryResultArticle(
            id="start",
            title="Start",
            description="Start Command",
            input_message_content=InputTextMessageContent(query.upper())
        ),
        InlineQueryResultArticle(
            id="inTrade",
            title="In Trade",
            description="Send a player full name to find all trades with that player",
            input_message_content=InputTextMessageContent(query.lower())
        ),
    ]

    await update.inline_query.answer(results)

async def in_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide a player name, e.g. /inTrade Garrett Wilson"
        )
        return
    
    client = SleeperClient(OSU_DYNASTY_LEAGUE_ID)
    roster_name_map = client.get_roster_name_map()

    player_name = " ".join(context.args)
    player_id = get_player_id(player_name)

    if not player_id:
        await update.message.reply_text(f"Player '{player_name}' not found.")
        return

    # Find all trades involving this player
    trades = find_trades_for_player(
        client.get_transactions,
        player_id
    )

    if not trades:
        await update.message.reply_text(
            f"No trades found involving {player_name}."
        )
        return

    # Send one message per trade
    for trade in trades:
        assets_by_roster = extract_trade_details(trade)

        msg_lines = [f"Week {trade['week']}"]

        for roster_id, assets in assets_by_roster.items():
            team_name = roster_name_map.get(roster_id, f"Team {roster_id}")
            msg_lines.append(f"\n{team_name} received:")

            for asset in assets:
                if asset["type"] == "player":
                    msg_lines.append(f"- {asset['name']}")
                elif asset["type"] == "pick":
                    msg_lines.append(
                        f"- {asset['season']} Round {asset['round']} Pick"
                    )

        await update.message.reply_text("\n".join(msg_lines))

if __name__ == '__main__':
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    inline_caps_handler = InlineQueryHandler(inline_query)
    inTrade_handler = CommandHandler('inTrade', in_trade)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)
    application.add_handler(inTrade_handler)
    application.add_handler(unknown_handler)
    
    application.run_polling()

