# Quick Start Guide

Get the DIY Repair Diagnosis API running in 5 minutes!

## Step 1: Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it (you'll need it in the next step)

## Step 2: Configure Environment

Create a `.env` file:

**On Windows:**
```cmd
copy .env.example .env
notepad .env
```

**On Mac/Linux:**
```bash
cp .env.example .env
nano .env
```

Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

Save and close the file.

## Step 3: Choose Your Method

### Option A: Docker (Recommended)

```bash
# Build the image
docker build -t diy-diagnosis .

# Run the container
docker run -p 8000:8000 --env-file .env diy-diagnosis
```

Then open: http://localhost:8000

### Option B: Python (Local Development)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --reload
```

Or use the startup script:
- **Windows**: Double-click `start.bat`
- **Mac/Linux**: `chmod +x start.sh && ./start.sh`

Then open: http://localhost:8000

## Step 4: Test It Out!

1. Open http://localhost:8000 in your browser
2. Upload a photo of something broken (or use a test image)
3. Review the diagnosis and repair instructions
4. Click **ℹ️ Details** to see performance metrics and OpenAI cost
5. Ask follow-up questions like "What tools do I need?"

## Performance & Costs

### First Request (No Cache)
- **Expected time**: 2-3 seconds
- **OpenAI cost**: ~$0.018 per request
- Click **ℹ️ Details** to see full breakdown

### Cached Request (Identical Image)
- **Expected time**: < 0.5 seconds
- **OpenAI cost**: $0.00 (served from cache!)
- Shows "Cached" status

### Follow-up Questions
- **Expected time**: 1.5-2 seconds
- **OpenAI cost**: ~$0.009 per question
- Smaller context = lower cost

### Saving Money with Cache
The cache is your friend! Uploading the same or similar image multiple times is **free** and **10x faster**.

## Common Issues

### "Module not found" error
```bash
pip install -r requirements.txt
```

### ".env file not found" error
Make sure you created the `.env` file (see Step 2)

### "Invalid API key" error
Check that your OpenAI API key is correct in `.env`

### Port 8000 already in use
Change the port in the command:
```bash
# Docker
docker run -p 8001:8000 --env-file .env diy-diagnosis

# Python
uvicorn app.main:app --port 8001
```

Then visit: http://localhost:8001

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Check [API documentation](http://localhost:8000/docs) for programmatic access
- Explore the code to understand how it works
- Customize the prompts in `app/prompts/` for your use case

## Need Help?

- Check the full README.md for troubleshooting
- Review the API docs at http://localhost:8000/docs
- Open an issue on GitHub

---

**Happy fixing! 🔧**
