# NASA TEMPO Air Quality API - Environment Setup

# Create and copy .env file
Copy-Item .env.example .env

# Install Python dependencies
.venv\Scripts\activate
pip install -r requirements.txt

# Initialize database (when ready)
# python scripts\init_db.py

# Run data collection script
# python scripts\collect_data.py

# Start the development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload