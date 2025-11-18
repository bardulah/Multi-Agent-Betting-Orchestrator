"""
Notification Agent
Sends betting recommendations via email or Telegram
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class NotificationAgent:
    """
    Agent that sends notifications about betting recommendations
    """

    def __init__(self, config: Dict):
        self.config = config
        self.notifications_enabled = config.get('notifications', {}).get('enabled', False)
        self.method = config.get('notifications', {}).get('method', 'email')

    def send_notifications(self, recommendations: List[Dict]) -> bool:
        """
        Send notifications for betting recommendations

        Args:
            recommendations: List of betting recommendations

        Returns:
            Success status
        """
        if not self.notifications_enabled:
            logger.info("Notifications disabled, skipping")
            return True

        # Filter for BET recommendations only
        bets = [r for r in recommendations if r.get('recommendation') == 'BET']

        if not bets:
            logger.info("No bets to notify about")
            return True

        logger.info(f"Sending notifications for {len(bets)} betting recommendations")

        success = True
        if self.method in ['email', 'both']:
            success = success and self._send_email(bets)

        if self.method in ['telegram', 'both']:
            success = success and self._send_telegram(bets)

        return success

    def _send_email(self, bets: List[Dict]) -> bool:
        """Send email notification"""
        try:
            email_config = self.config.get('notifications', {}).get('email', {})
            smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_config.get('smtp_port', 587)
            sender_email = email_config.get('sender_email')
            sender_password = os.getenv('EMAIL_PASSWORD') or email_config.get('sender_password')
            recipient_email = email_config.get('recipient_email')

            if not all([sender_email, sender_password, recipient_email]):
                logger.warning("Email configuration incomplete, skipping email notification")
                return False

            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = f"Betting Recommendations - {datetime.now().strftime('%Y-%m-%d')}"
            message['From'] = sender_email
            message['To'] = recipient_email

            # Create email body
            text_body = self._create_text_email_body(bets)
            html_body = self._create_html_email_body(bets)

            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')

            message.attach(text_part)
            message.attach(html_part)

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _send_telegram(self, bets: List[Dict]) -> bool:
        """Send Telegram notification"""
        try:
            telegram_config = self.config.get('notifications', {}).get('telegram', {})
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or telegram_config.get('bot_token')
            chat_id = os.getenv('TELEGRAM_CHAT_ID') or telegram_config.get('chat_id')

            if not all([bot_token, chat_id]):
                logger.warning("Telegram configuration incomplete, skipping Telegram notification")
                return False

            # Create message
            message = self._create_telegram_message(bets)

            # Send via Telegram Bot API
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            logger.info(f"Telegram message sent successfully to chat {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _create_text_email_body(self, bets: List[Dict]) -> str:
        """Create plain text email body"""
        lines = [
            f"Betting Recommendations - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            f"Total Recommendations: {len(bets)}",
            ""
        ]

        for i, bet in enumerate(bets, 1):
            lines.extend([
                f"BET #{i}",
                "-" * 40,
                f"Match: {bet['homeTeam']} vs {bet['awayTeam']}",
                f"Sport: {bet['sport']} | League: {bet.get('league', 'Unknown')}",
                f"Time: {bet.get('time', 'TBD')}",
                f"",
            ])

            # Add all 3 layers of picks
            if bet.get('internet_picks'):
                internet = bet['internet_picks']
                lines.extend([
                    f"🌐 INTERNET PICKS (Community consensus)",
                    f"   Picks: {', '.join(internet.get('picks', []))}",
                    f"   Confidence: {internet.get('confidence', 0.0):.1%}",
                    f"   Analysis: {internet.get('analysis', 'N/A')}",
                    f""
                ])

            if bet.get('data_driven'):
                data_driven = bet['data_driven']
                lines.extend([
                    f"📊 DATA-DRIVEN (Statistical analysis)",
                    f"   Picks: {', '.join(data_driven.get('picks', []))}",
                    f"   Confidence: {data_driven.get('confidence', 0.0):.1%}",
                    f"   Analysis: {data_driven.get('analysis', 'N/A')}",
                    f""
                ])

            # Final synthesis recommendation
            lines.extend([
                f"🎯 FINAL RECOMMENDATION (3-Layer Synthesis)",
                f"   Pick: {bet.get('recommended_pick', 'N/A').upper()}",
                f"   Odds Target: {bet.get('recommended_odds', 'N/A')}",
                f"   Confidence: {bet.get('confidence', 0.0):.1%}",
                f"   Agreement Score: {bet.get('agreement_score', 0.0):.1%}",
                f"",
                f"Detailed Reasoning:",
                bet.get('reasoning', 'No reasoning provided'),
                f"",
                f"Value Assessment:",
                bet.get('value_assessment', 'N/A'),
                "",
                ""
            ])

        lines.extend([
            "",
            "=" * 60,
            "Good luck with your bets!",
            "",
            "Disclaimer: These are automated recommendations. Always do your own research.",
            "Never bet more than you can afford to lose."
        ])

        return "\n".join(lines)

    def _create_html_email_body(self, bets: List[Dict]) -> str:
        """Create HTML email body"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .bet-card {{
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                    background-color: #ecf0f1;
                }}
                .match-info {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
                .pick {{ color: #27ae60; font-weight: bold; font-size: 16px; }}
                .confidence {{ color: #e74c3c; font-weight: bold; }}
                .meta {{ color: #7f8c8d; font-size: 14px; }}
                .reasoning {{ margin-top: 10px; padding: 10px; background-color: white; border-radius: 5px; }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #95a5a6; }}
            </style>
        </head>
        <body>
            <h1>🎯 Betting Recommendations</h1>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Total Recommendations:</strong> {len(bets)}</p>
        """

        for i, bet in enumerate(bets, 1):
            confidence_color = "green" if bet.get('confidence', 0) > 0.7 else "orange" if bet.get('confidence', 0) > 0.5 else "red"

            html += f"""
            <div class="bet-card">
                <h2>BET #{i}</h2>
                <div class="match-info">
                    {bet['homeTeam']} vs {bet['awayTeam']}
                </div>
                <div class="meta">
                    {bet['sport']} | {bet.get('league', 'Unknown')} | {bet.get('time', 'TBD')}
                </div>
            """

            # Add Internet Picks layer
            if bet.get('internet_picks'):
                internet = bet['internet_picks']
                picks_html = ', '.join(internet.get('picks', []))
                html += f"""
                <div style="border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; background-color: #d6eaf8;">
                    <strong>🌐 Internet Picks (Community)</strong><br>
                    <strong>Picks:</strong> {picks_html}<br>
                    <strong>Confidence:</strong> {internet.get('confidence', 0.0):.1%}<br>
                    <strong>Analysis:</strong> {internet.get('analysis', 'N/A')[:500]}
                </div>
                """

            # Add Data-Driven layer
            if bet.get('data_driven'):
                data_driven = bet['data_driven']
                picks_html = ', '.join(data_driven.get('picks', []))
                html += f"""
                <div style="border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; background-color: #fadbd8;">
                    <strong>📊 Data-Driven (Statistical)</strong><br>
                    <strong>Picks:</strong> {picks_html}<br>
                    <strong>Confidence:</strong> {data_driven.get('confidence', 0.0):.1%}<br>
                    <strong>Analysis:</strong> {data_driven.get('analysis', 'N/A')[:500]}
                </div>
                """

            # Final synthesis recommendation
            html += f"""
                <div style="border-left: 4px solid #27ae60; padding: 10px; margin: 10px 0; background-color: #d5f4e6;">
                    <strong>🎯 Final Recommendation (3-Layer Synthesis)</strong><br>
                    <span class="pick">Pick: {bet.get('recommended_pick', 'N/A').upper()} @ {bet.get('recommended_odds', 'N/A')}</span><br>
                    <span class="confidence" style="color: {confidence_color};">Confidence: {bet.get('confidence', 0.0):.1%}</span> | Agreement: {bet.get('agreement_score', 0.0):.1%}
                </div>
                <div class="reasoning">
                    <strong>Detailed Reasoning:</strong><br>
                    {bet.get('reasoning', 'No reasoning provided')}
                </div>
                <p><strong>Value Assessment:</strong> {bet.get('value_assessment', 'N/A')}</p>
            </div>
            """

        html += """
            <div class="footer">
                <p><strong>Disclaimer:</strong> These are automated recommendations based on data analysis and internet sources.
                Always conduct your own research before placing bets. Never bet more than you can afford to lose.</p>
                <p>Good luck! 🍀</p>
            </div>
        </body>
        </html>
        """

        return html

    def _create_telegram_message(self, bets: List[Dict]) -> str:
        """Create Telegram message"""
        lines = [
            f"🎯 <b>Betting Recommendations</b>",
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"<b>Total: {len(bets)} recommendations</b>",
            ""
        ]

        for i, bet in enumerate(bets, 1):
            confidence_emoji = "🟢" if bet.get('confidence', 0) > 0.7 else "🟡" if bet.get('confidence', 0) > 0.5 else "🔴"

            lines.extend([
                f"<b>BET #{i}</b>",
                f"⚽ {bet['homeTeam']} vs {bet['awayTeam']}",
                f"🏆 {bet['sport']} | {bet.get('league', 'Unknown')}",
                f""
            ])

            # Internet Picks layer (concise for Telegram)
            if bet.get('internet_picks'):
                internet = bet['internet_picks']
                lines.append(f"🌐 Internet: {', '.join(internet.get('picks', []))} ({internet.get('confidence', 0.0):.0%})")

            # Data-Driven layer (concise for Telegram)
            if bet.get('data_driven'):
                data_driven = bet['data_driven']
                lines.append(f"📊 Data-Driven: {', '.join(data_driven.get('picks', []))} ({data_driven.get('confidence', 0.0):.0%})")

            # Final pick
            lines.extend([
                f"",
                f"✅ <b>Final Pick:</b> {bet.get('recommended_pick', 'N/A').upper()} @ {bet.get('recommended_odds', 'N/A')}",
                f"{confidence_emoji} <b>Confidence:</b> {bet.get('confidence', 0.0):.0%} | Agreement: {bet.get('agreement_score', 0.0):.0%}",
                f"",
                f"💭 {bet.get('reasoning', 'No reasoning')[:150]}",
                f"",
                "➖" * 20,
                ""
            ])

        lines.extend([
            "",
            "⚠️ <i>Automated recommendations. DYOR. Bet responsibly.</i>"
        ])

        return "\n".join(lines)

    def send_test_notification(self) -> bool:
        """Send a test notification"""
        test_bet = {
            'homeTeam': 'Test Team A',
            'awayTeam': 'Test Team B',
            'sport': 'football',
            'league': 'Test League',
            'time': '15:00',
            'recommendation': 'BET',
            'recommended_pick': 'home_win',
            'recommended_odds': 2.10,
            'confidence': 0.75,
            'agreement_score': 0.85,
            'reasoning': 'This is a test notification to verify the system is working correctly.',
            'value_assessment': 'Good value based on analysis'
        }

        logger.info("Sending test notification")
        return self.send_notifications([test_bet])
