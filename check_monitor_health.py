import sys
import os

# Add parent directory to path
sys.path.append('..')

try:
    from services import monitor_health
    print(f'Found monitor_health at: {monitor_health.__file__}')
    
    # Check if MonitorHealth class exists
    if hasattr(monitor_health, 'MonitorHealth'):
        print('MonitorHealth class exists in the module')
    else:
        print('MonitorHealth class does not exist in the module')
        
except Exception as e:
    print(f'Error importing monitor_health: {e}') 