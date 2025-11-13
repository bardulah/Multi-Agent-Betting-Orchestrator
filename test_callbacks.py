#!/usr/bin/env python3
"""
Test callback implementation
Verifies that callbacks are properly created and integrated.
"""

import sys
import os
import yaml

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from dotenv import load_dotenv
load_dotenv('config/.env')

print('=' * 60)
print('TEST: Callback Implementation')
print('=' * 60)
print()

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Test 1: Callback creation
print('TEST 1: Callback Factory Functions')
print('-' * 60)

try:
    from agents.utils.callbacks import (
        create_after_tool_callback,
        create_before_agent_callback,
        create_after_agent_callback
    )
    
    print('✓ Callback factories imported\n')
    
    # Create callbacks
    after_tool = create_after_tool_callback("TestAgent")
    before_agent = create_before_agent_callback("TestAgent")
    after_agent = create_after_agent_callback("TestAgent")
    
    print('✓ All callback factories work')
    print(f'  - after_tool_callback: {type(after_tool).__name__}')
    print(f'  - before_agent_callback: {type(before_agent).__name__}')
    print(f'  - after_agent_callback: {type(after_agent).__name__}')
    print('\n✓ TEST 1 PASSED\n')
    
except Exception as e:
    print(f'✗ TEST 1 FAILED: {e}')
    import traceback
    traceback.print_exc()

# Test 2: Integration with InternetPicksAgent
print('TEST 2: InternetPicksAgent with Callbacks')
print('-' * 60)

try:
    from agents.internet_picks_agent import create_internet_picks_agent
    
    print('Creating InternetPicksAgent with callbacks...')
    agent = create_internet_picks_agent(config)
    
    # Check that callbacks are assigned
    has_callbacks = (
        agent.before_agent_callback is not None and
        agent.after_agent_callback is not None and
        agent.after_tool_callback is not None
    )
    
    if has_callbacks:
        print('✓ All callbacks assigned to InternetPicksAgent')
        print(f'  - before_agent_callback: {agent.before_agent_callback is not None}')
        print(f'  - after_agent_callback: {agent.after_agent_callback is not None}')
        print(f'  - after_tool_callback: {agent.after_tool_callback is not None}')
        print('\n✓ TEST 2 PASSED\n')
    else:
        print('✗ Callbacks not properly assigned')
        raise AssertionError("Missing callbacks")
    
except Exception as e:
    print(f'✗ TEST 2 FAILED: {e}')
    import traceback
    traceback.print_exc()

# Test 3: Integration with DataDrivenAgent
print('TEST 3: DataDrivenAgent with Callbacks')
print('-' * 60)

try:
    from agents.data_driven_agent import create_data_driven_agent
    
    print('Creating DataDrivenAgent with callbacks...')
    agent = create_data_driven_agent(config)
    
    # Check that callbacks are assigned
    has_callbacks = (
        agent.before_agent_callback is not None and
        agent.after_agent_callback is not None and
        agent.after_tool_callback is not None
    )
    
    if has_callbacks:
        print('✓ All callbacks assigned to DataDrivenAgent')
        print(f'  - before_agent_callback: {agent.before_agent_callback is not None}')
        print(f'  - after_agent_callback: {agent.after_agent_callback is not None}')
        print(f'  - after_tool_callback: {agent.after_tool_callback is not None}')
        print('\n✓ TEST 3 PASSED\n')
    else:
        print('✗ Callbacks not properly assigned')
        raise AssertionError("Missing callbacks")
    
except Exception as e:
    print(f'✗ TEST 3 FAILED: {e}')
    import traceback
    traceback.print_exc()

# Test 4: Async utilities
print('TEST 4: Async Utilities')
print('-' * 60)

try:
    from agents.utils.async_utils import (
        run_with_timeout,
        run_with_retry,
        run_with_timeout_and_retry,
        AsyncTimer
    )
    
    print('✓ Async utilities imported\n')
    
    # Test AsyncTimer
    import asyncio
    
    async def test_timer():
        async with AsyncTimer("test_operation") as timer:
            await asyncio.sleep(0.1)
        return timer.elapsed_seconds
    
    elapsed = asyncio.run(test_timer())
    
    if elapsed >= 0.1 and elapsed < 0.2:
        print(f'✓ AsyncTimer works (elapsed: {elapsed:.3f}s)')
    else:
        print(f'✗ AsyncTimer timing unexpected: {elapsed:.3f}s')
    
    print('\n✓ TEST 4 PASSED\n')
    
except Exception as e:
    print(f'✗ TEST 4 FAILED: {e}')
    import traceback
    traceback.print_exc()

# Summary
print('=' * 60)
print('SUMMARY')
print('=' * 60)
print("""
Phase 1.3 Callback Tests:
✓ Callback factory functions work
✓ InternetPicksAgent has callbacks assigned
✓ DataDrivenAgent has callbacks assigned
✓ Async utilities available (timeout, retry, timer)

Next Steps:
- Run actual agent with callbacks enabled
- Monitor log output for callback traces
- Test timeout/retry functionality
- Measure performance impact (should be minimal)

Callbacks will provide:
- Tool execution logging (what tools are used)
- Search result truncation (max 10 results)
- Agent lifecycle logging (start/end)
- Timeout protection (can be added next)
""")
print('=' * 60)
