#!/usr/bin/env python3
"""
Telegram Bot for Multi-Agent Betting System
Provides mobile access to betting analysis via Telegram
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from dotenv import load_dotenv
from agents.utils.logging_config import get_logger
from bot_integration import ResultsLoader, ResultFormatter, BetPaginator, AnalysisRunner

# Setup logging
logger = get_logger(__name__)

# Load environment variables
load_dotenv('config/.env')


class BettingBotHandler:
    """Handle Telegram bot interactions"""

    def __init__(self):
        """Initialize bot handler"""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

        self.results_loader = ResultsLoader()
        self.formatter = ResultFormatter()
        self.analysis_runner = AnalysisRunner()

        # Store pagination state per user
        self.user_paginators = {}

        # Store analysis state per user (for tracking running analysis)
        self.user_analysis_state = {}

        logger.info("Telegram Bot Handler initialized")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command - show welcome message and main menu"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.first_name}) started bot")

        welcome_text = """🎯 Welcome to Multi-Agent Betting System!

I can help you:
• 📊 View betting recommendations
• 🔍 Trigger new analysis
• 🏆 Filter by sport
• ⚙️ Manage settings

Select an action below to get started:"""

        keyboard = [
            [
                InlineKeyboardButton("📊 Show Results", callback_data="show_today"),
                InlineKeyboardButton("🔍 Analyze", callback_data="analyze"),
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command - show available commands"""
        user = update.effective_user
        logger.info(f"User {user.id} requested help")

        help_text = """📖 <b>Available Commands</b>

<b>Main Commands:</b>
/start - Show main menu
/analyze - Trigger new analysis
/show - View recommendations
/filter - Filter by sport
/settings - Configure preferences
/help - Show this message

<b>Quick Examples:</b>
/analyze - Run analysis on all sports
/show today - Show today's recommendations
/show tomorrow - Show tomorrow's recommendations
/filter football - Show only football bets
/settings - Adjust confidence threshold

<b>Interactive Navigation:</b>
Use the buttons that appear in messages for easy navigation on mobile."""

        await update.message.reply_text(help_text, parse_mode="HTML")

    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle help button from main menu"""
        query = update.callback_query
        await query.answer()

        help_text = """📖 <b>Available Commands</b>

<b>Main Commands:</b>
/start - Show main menu
/analyze - Trigger new analysis
/show - View recommendations
/filter - Filter by sport
/settings - Configure preferences
/help - Show this message

<b>Quick Examples:</b>
/analyze - Run analysis on all sports
/show today - Show today's recommendations
/show tomorrow - Show tomorrow's recommendations
/filter football - Show only football bets

<b>Interactive Navigation:</b>
Use the buttons that appear in messages for easy navigation."""

        keyboard = [
            [InlineKeyboardButton("◀️ Back to Menu", callback_data="start_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

    async def start_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle back to menu button"""
        query = update.callback_query
        await query.answer()

        welcome_text = """🎯 <b>Multi-Agent Betting System</b>

Select an action below:"""

        keyboard = [
            [
                InlineKeyboardButton("📊 Show Results", callback_data="show_today"),
                InlineKeyboardButton("🔍 Analyze", callback_data="analyze"),
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback query (button press)"""
        query = update.callback_query
        callback_data = query.data
        user_id = update.effective_user.id

        logger.info(f"Button pressed: {callback_data} by user {user_id}")

        # Route to appropriate handler
        if callback_data == "help":
            await self.help_callback(update, context)
        elif callback_data == "start_menu":
            await self.start_menu_callback(update, context)
        elif callback_data == "show_today":
            await self.show_results_callback(update, context, "today")
        elif callback_data == "show_next":
            await self.show_next_callback(update, context)
        elif callback_data == "show_prev":
            await self.show_prev_callback(update, context)
        elif callback_data == "show_status":
            await self.show_status_callback(update, context)
        elif callback_data == "analyze":
            await self.analyze_callback(update, context)
        elif callback_data.startswith("analyze_"):
            sport = callback_data.replace("analyze_", "")
            await self.run_analysis_for_sport(update, context, sport)
        elif callback_data == "settings":
            await self.settings_callback(update, context)
        else:
            await query.answer("Command not yet implemented", show_alert=False)

    async def show_results_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, date: str = "today"
    ) -> None:
        """Handle showing results"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id

        # Load results
        results = self.results_loader.load_results(date)

        if not results:
            message = f"""❌ <b>No recommendations available for {date.upper()}</b>

Please run analysis first with /analyze"""

            keyboard = [
                [InlineKeyboardButton("🔍 Run Analysis", callback_data="analyze")],
                [InlineKeyboardButton("◀️ Back", callback_data="start_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
            return

        # Get BET recommendations
        recommendations = results.get('recommendations', [])
        bet_recommendations = [r for r in recommendations if r.get('recommendation') == 'BET']

        if not bet_recommendations:
            message = f"""📊 <b>Recommendations for {date.upper()}</b>

No BET recommendations found.
({len(recommendations)} matches analyzed, all marked as NO_BET or HOLD)"""

            keyboard = [
                [InlineKeyboardButton("🔍 Run New Analysis", callback_data="analyze")],
                [InlineKeyboardButton("◀️ Back", callback_data="start_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
            return

        # Create paginator and store for user
        paginator = BetPaginator(bet_recommendations)
        self.user_paginators[user_id] = {'paginator': paginator, 'date': date}

        # Show first bet
        current_bet = paginator.get_current()
        message = self.formatter.format_full_bet(current_bet, number=1)
        message = f"📊 <b>Recommendations for {date.upper()}</b>\n\n" + message

        keyboard = []
        if paginator.has_prev() or paginator.has_next():
            nav_buttons = []
            if paginator.has_prev():
                nav_buttons.append(InlineKeyboardButton("◀️ Prev", callback_data="show_prev"))
            nav_buttons.append(InlineKeyboardButton(f"📄 {paginator.get_status()}", callback_data="show_status"))
            if paginator.has_next():
                nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="show_next"))
            keyboard.append(nav_buttons)

        keyboard.append([
            InlineKeyboardButton("🔍 New Analysis", callback_data="analyze"),
            InlineKeyboardButton("◀️ Back", callback_data="start_menu"),
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

    async def show_next_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle next button in pagination"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id

        if user_id not in self.user_paginators:
            await query.answer("Session expired. Please use /show to start again.", show_alert=True)
            return

        state = self.user_paginators[user_id]
        paginator = state['paginator']
        date = state['date']

        if paginator.next():
            current_bet = paginator.get_current()
            number = paginator.current_index + 1
            message = self.formatter.format_full_bet(current_bet, number=number)
            message = f"📊 <b>Recommendations for {date.upper()}</b>\n\n" + message

            keyboard = []
            nav_buttons = []
            if paginator.has_prev():
                nav_buttons.append(InlineKeyboardButton("◀️ Prev", callback_data="show_prev"))
            nav_buttons.append(InlineKeyboardButton(f"📄 {paginator.get_status()}", callback_data="show_status"))
            if paginator.has_next():
                nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="show_next"))
            keyboard.append(nav_buttons)

            keyboard.append([
                InlineKeyboardButton("🔍 New Analysis", callback_data="analyze"),
                InlineKeyboardButton("◀️ Back", callback_data="start_menu"),
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

    async def show_prev_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle previous button in pagination"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id

        if user_id not in self.user_paginators:
            await query.answer("Session expired. Please use /show to start again.", show_alert=True)
            return

        state = self.user_paginators[user_id]
        paginator = state['paginator']
        date = state['date']

        if paginator.prev():
            current_bet = paginator.get_current()
            number = paginator.current_index + 1
            message = self.formatter.format_full_bet(current_bet, number=number)
            message = f"📊 <b>Recommendations for {date.upper()}</b>\n\n" + message

            keyboard = []
            nav_buttons = []
            if paginator.has_prev():
                nav_buttons.append(InlineKeyboardButton("◀️ Prev", callback_data="show_prev"))
            nav_buttons.append(InlineKeyboardButton(f"📄 {paginator.get_status()}", callback_data="show_status"))
            if paginator.has_next():
                nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="show_next"))
            keyboard.append(nav_buttons)

            keyboard.append([
                InlineKeyboardButton("🔍 New Analysis", callback_data="analyze"),
                InlineKeyboardButton("◀️ Back", callback_data="start_menu"),
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

    async def show_status_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle status button - just show a toast"""
        query = update.callback_query
        user_id = update.effective_user.id

        if user_id not in self.user_paginators:
            await query.answer("Session expired.")
            return

        state = self.user_paginators[user_id]
        paginator = state['paginator']
        await query.answer(f"Viewing {paginator.get_status()}", show_alert=False)

    async def run_analysis_for_sport(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, sport: str
    ) -> None:
        """Run analysis for specific sport"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id

        # Map sport codes to sport names
        sport_map = {
            'all': None,
            'football': ['football'],
            'basketball': ['basketball'],
            'tennis': ['tennis'],
            'hockey': ['hockey'],
        }

        sports_list = sport_map.get(sport, None)

        # Show progress message
        if sport == 'all':
            message = """🔍 <b>Running Analysis</b>

📊 Analyzing all sports...
⏳ This may take 5-15 minutes.

Please wait...
"""
        else:
            sport_name = sport.upper()
            message = f"""🔍 <b>Running Analysis</b>

📊 Analyzing {sport_name}...
⏳ This may take 2-5 minutes.

Please wait...
"""

        keyboard = [
            [InlineKeyboardButton("📊 Back to Menu", callback_data="start_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

        # Track analysis state
        self.user_analysis_state[user_id] = {
            'sport': sport,
            'status': 'running',
            'message_id': query.message.message_id
        }

        logger.info(f"User {user_id} started analysis for: {sport}")

        # Run analysis asynchronously
        success = await self.analysis_runner.run_analysis(
            date="today",
            sports=sports_list
        )

        # Update message with result
        if success:
            result_message = """✅ <b>Analysis Complete!</b>

🎯 New recommendations have been generated.

Tap below to view the latest results:"""

            keyboard = [
                [InlineKeyboardButton("📊 Show Results", callback_data="show_today")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="start_menu")],
            ]
        else:
            result_message = """❌ <b>Analysis Failed</b>

There was an error running the analysis.
Please check the logs or try again later.

Check /help for more information."""

            keyboard = [
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="start_menu")],
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Try to update the original message
        try:
            await query.edit_message_text(result_message, reply_markup=reply_markup, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to update message: {e}")

        # Clean up state
        if user_id in self.user_analysis_state:
            del self.user_analysis_state[user_id]

    async def analyze_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle analyze button - show analysis options"""
        query = update.callback_query
        await query.answer()

        message = """🔍 <b>Run Analysis</b>

Select what to analyze:"""

        keyboard = [
            [
                InlineKeyboardButton("⚽ All Sports", callback_data="analyze_all"),
                InlineKeyboardButton("🏀 Basketball", callback_data="analyze_basketball"),
            ],
            [
                InlineKeyboardButton("⚽ Football", callback_data="analyze_football"),
                InlineKeyboardButton("🎾 Tennis", callback_data="analyze_tennis"),
            ],
            [
                InlineKeyboardButton("🏒 Hockey", callback_data="analyze_hockey"),
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="start_menu"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

    async def settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle settings button"""
        query = update.callback_query
        await query.answer()

        message = """⚙️ <b>Settings</b>

<i>Settings feature is being implemented</i>

Available settings:
• Confidence threshold
• Notification method
• Sports filter"""

        keyboard = [
            [InlineKeyboardButton("◀️ Back", callback_data="start_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

    async def unknown_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle unknown commands"""
        user = update.effective_user
        logger.warning(f"Unknown command from {user.id}: {update.message.text}")

        await update.message.reply_text(
            "❌ Unknown command. Type /help to see available commands."
        )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors caused by Updates"""
        logger.error(f"Exception while handling an update: {context.error}")


async def main():
    """Start the Telegram bot"""
    logger.info("Starting Telegram Bot...")

    # Initialize handler
    handler = BettingBotHandler()

    # Create application
    application = Application.builder().token(handler.token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", handler.start))
    application.add_handler(CommandHandler("help", handler.help_command))
    application.add_handler(CommandHandler("analyze", handler.analyze_callback))
    application.add_handler(CallbackQueryHandler(handler.button_callback))
    application.add_error_handler(handler.error_handler)
    application.add_handler(
        MessageHandler(filters.COMMAND, handler.unknown_command)
    )

    # Start the bot
    logger.info("Telegram bot is running. Press Ctrl+C to stop.")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_bot():
    """Run the bot with proper event loop handling"""
    try:
        # Try to get the existing event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're already in an async context
            logger.error("Cannot run bot in existing event loop. Use 'asyncio.run(main())' or run as standalone script")
            return False
        except RuntimeError:
            # No running loop, safe to create one
            asyncio.run(main())
            return True
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    run_bot()
