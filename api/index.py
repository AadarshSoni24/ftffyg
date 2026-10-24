import sys
from pathlib import Path

# Add root directory to PYTHONPATH for Vercel Serverless Function
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.main import app
