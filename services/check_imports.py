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
        
        # Check _get_iso_timestamp method
        monitor = monitor_health.MonitorHealth()
        try:
            timestamp = monitor._get_iso_timestamp()
            print(f'_get_iso_timestamp() returned: {timestamp}')
        except Exception as e:
            print(f'Error calling _get_iso_timestamp(): {e}')
    else:
        print('MonitorHealth class does not exist in the module')
        
    # Check module contents
    print('\nmonitor_health module contents:')
    for item in dir(monitor_health):
        if not item.startswith('__'):
            print(f'  - {item}')
            
except Exception as e:
    print(f'\nError importing monitor_health: {e}')

# Try to import directly from the actual file path
try:
    print('\nTrying to import from ../services/monitor_health.py')
    import importlib.util
    spec = importlib.util.spec_from_file_location('monitor_health', 
                                                 os.path.join(os.path.abspath('..'), 'services', 'monitor_health.py'))
    if spec:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print('Successfully imported module directly from file')
        print('Module contents:')
        for item in dir(module):
            if not item.startswith('__'):
                print(f'  - {item}')
    else:
        print('Could not find monitor_health.py file')
except Exception as e:
    print(f'Error importing directly from file: {e}')