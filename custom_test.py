import asyncio
from agents.internet_picks_agent import InternetPicksAgent

async def test_custom_match():
    config = {}
    agent = InternetPicksAgent(config)
    
    # Test with ANY match you want
    match = {
        'homeTeam': 'Barcelona',
        'awayTeam': 'Real Madrid',
        'sport': 'football',
        'id': 'el_clasico_test'
    }
    
    print(f"🎯 Testing: {match['homeTeam']} vs {match['awayTeam']}")
    result = await agent.analyze_match_async(match)
    
    print(f"Analysis: {result.get('analysis', '')[:300]}...")
    print(f"Confidence: {result.get('confidence', 0):.0%}")
    print(f"Pick: {result.get('picks', [])}")

asyncio.run(test_custom_match())
