#!/usr/bin/env python3
"""
Interactive Chat Interface for Betting System Analysis
Allows users to ask questions about matches, recommendations, and value bets
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

# Load environment
load_dotenv('config/.env')

colorama.init(autoreset=True)

# Configure Google GenAI
google_api_key = os.getenv('GOOGLE_API_KEY')
if google_api_key:
    genai.configure(api_key=google_api_key)


class BettingAnalysisChat:
    """Interactive chat interface for betting system analysis"""

    def __init__(self):
        # Load config
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)

        # Load results if available
        self.load_latest_results()

        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def load_latest_results(self):
        """Load the latest betting recommendations"""
        results_path = Path('data/results.json')
        history_path = Path('data/history.json')
        matches_path = Path('data/matches.json')

        self.latest_results = None
        self.history = None
        self.matches = None

        if results_path.exists():
            with open(results_path) as f:
                self.latest_results = json.load(f)

        if history_path.exists():
            with open(history_path) as f:
                self.history = json.load(f)

        if matches_path.exists():
            with open(matches_path) as f:
                self.matches = json.load(f)

    def format_recommendations(self) -> str:
        """Format the latest recommendations for display"""
        if not self.latest_results:
            return "No recommendations available yet. Run the betting system first."

        output = []
        output.append(f"\n{Fore.CYAN}Latest Recommendations (as of {self.latest_results.get('timestamp', 'Unknown')}){Style.RESET_ALL}")
        output.append(f"Total matches: {self.latest_results.get('total_matches', 0)}")
        output.append(f"Recommended bets: {self.latest_results.get('bets_recommended', 0)}\n")

        for rec in self.latest_results.get('recommendations', [])[:10]:  # Show top 10
            status = f"{Fore.GREEN}✓ BET{Style.RESET_ALL}" if rec.get('recommendation') == 'BET' else f"{Fore.YELLOW}✗ NO_BET{Style.RESET_ALL}"
            output.append(f"{status} | {rec['homeTeam']} vs {rec['awayTeam']}")
            output.append(f"    Sport: {rec['sport']} | Confidence: {rec['confidence']:.1%}")
            if rec.get('recommended_pick'):
                output.append(f"    Pick: {rec['recommended_pick']} @ {rec.get('recommended_odds', 'N/A')}")
            output.append("")

        return "\n".join(output)

    def chat(self):
        """Main chat loop"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🎲 Betting System Chat Interface{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Ask questions about matches, recommendations, value bets, and more!{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}Type 'exit' to quit, 'show' to see latest bets, 'help' for commands{Style.RESET_ALL}\n")

        # Show initial recommendations
        print(self.format_recommendations())

        while True:
            try:
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()

                if not user_input:
                    continue

                if user_input.lower() == 'exit':
                    print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break

                if user_input.lower() == 'show':
                    self.load_latest_results()
                    print(self.format_recommendations())
                    continue

                if user_input.lower() == 'help':
                    self.show_help()
                    continue

                # Process question with agent
                print(f"\n{Fore.CYAN}Agent: {Style.RESET_ALL}", end="", flush=True)
                response = self.get_agent_response(user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

    def get_agent_response(self, question: str) -> str:
        """Get response from the model"""
        try:
            # Prepare context from loaded data
            context = self._prepare_agent_context(question)

            # Call the model
            response = self.model.generate_content(context)
            return response.text

        except Exception as e:
            return f"I encountered an error while processing your question: {str(e)}"

    def _prepare_agent_context(self, question: str) -> str:
        """Prepare context for the agent response"""
        context_parts = []

        context_parts.append("You are a professional sports betting analyst helping someone understand betting recommendations and match analysis.")
        context_parts.append("\nCURRENT DATA AVAILABLE:")

        if self.latest_results:
            context_parts.append(f"\nLatest Recommendations (as of {self.latest_results.get('timestamp', 'Unknown')}):")
            context_parts.append(f"- Total matches analyzed: {self.latest_results.get('total_matches', 0)}")
            context_parts.append(f"- Bets recommended: {self.latest_results.get('bets_recommended', 0)}")

            # Add top recommendations
            if self.latest_results.get('recommendations'):
                context_parts.append("\nTop Recommendations:")
                for rec in self.latest_results.get('recommendations', [])[:5]:
                    context_parts.append(f"\n- {rec['homeTeam']} vs {rec['awayTeam']}")
                    context_parts.append(f"  Sport: {rec['sport']}")
                    context_parts.append(f"  Recommendation: {rec['recommendation']}")
                    context_parts.append(f"  Confidence: {rec['confidence']:.1%}")
                    if rec.get('recommended_pick'):
                        context_parts.append(f"  Pick: {rec['recommended_pick']} @ {rec.get('recommended_odds', 'N/A')}")
                    if rec.get('reasoning'):
                        context_parts.append(f"  Reasoning: {rec['reasoning'][:200]}...")
        else:
            context_parts.append("- No recommendations available yet")

        if self.matches:
            context_parts.append(f"\nTotal matches in database: {len(self.matches)}")

        context_parts.append(f"\nUSER QUESTION: {question}")
        context_parts.append("\nProvide a helpful, clear answer based on the available data. Be conversational but professional.")

        return "\n".join(context_parts)

    def show_help(self):
        """Show available commands"""
        help_text = f"""
{Fore.CYAN}{Style.BRIGHT}Available Commands:{Style.RESET_ALL}

- {Fore.GREEN}show{Style.RESET_ALL}     - Display latest betting recommendations
- {Fore.GREEN}help{Style.RESET_ALL}     - Show this help message
- {Fore.GREEN}exit{Style.RESET_ALL}     - Exit the chat

{Fore.CYAN}{Style.BRIGHT}Example Questions:{Style.RESET_ALL}

- "What are the best value bets today?"
- "Which matches have the highest confidence?"
- "Tell me about the Man City vs Arsenal match"
- "What's the system's recommendation for basketball games?"
- "Show me bets with over 70% confidence"
- "Which sport has the best opportunities?"
- "What was the system's last recommendation?"

"""
        print(help_text)


def main():
    """Main entry point"""
    try:
        chat = BettingAnalysisChat()
        chat.chat()
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
