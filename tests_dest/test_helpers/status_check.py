"""
Check available MaterialStatus enum values
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import MaterialStatus
from models.material import MaterialStatus

# Print out all available enum values
print(f"Available MaterialStatus values:")
for status in MaterialStatus:
    print(f"  - {status.name} = {status.value}")

# Print out specific attributes
print("\nTesting specific status values:")
for status_name in ["ACTIVE", "INACTIVE", "DEPRECATED", "OBSOLETE"]:
    try:
        status = getattr(MaterialStatus, status_name)
        print(f"  - MaterialStatus.{status_name} = {status}")
    except AttributeError:
        print(f"  - MaterialStatus.{status_name} doesn't exist")

# Also check if enum has __members__
if hasattr(MaterialStatus, "__members__"):
    print("\nMaterialStatus.__members__:")
    for name, member in MaterialStatus.__members__.items():
        print(f"  - {name} = {member}")

if __name__ == "__main__":
    pass 