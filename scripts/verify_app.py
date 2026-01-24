import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Verifying imports...")
    from app import app
    print("✅ App imported successfully.")
    
    print("Verifying routes...")
    from app.routes import evidence_routes
    print("✅ Evidence routes imported successfully.")
    
    print("SUCCESS: Codebase appears stable.")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)
except SyntaxError as e:
    print(f"❌ SyntaxError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
