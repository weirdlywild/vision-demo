# DIY Repair Diagnosis API

AI-powered visual diagnosis of broken household items with step-by-step repair instructions using GPT-4o Vision.

## Features

- **Chat Interface** - Beautiful, responsive chat UI for easy interaction
- **Image-based diagnosis** - Upload a photo, get a detailed repair plan
- **Performance Timing** - See exactly how long each step takes (OpenAI API, image processing, caching)
- **Generic materials only** - No brand names, SKUs, or URLs
- **Multi-turn conversations** - Ask follow-up questions with session context
- **Quality gate** - Automatic image validation to save API costs
- **High-performance caching** - Dual-level cache (exact + perceptual hashing)
- **Safety-first** - Comprehensive safety warnings for all repairs
- **Docker-ready** - Single command deployment

## Quick Start

### Prerequisites

- Docker
- OpenAI API key with GPT-4o access

### Run with Docker

1. Clone this repository
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
4. Build and run:
   ```bash
   docker build -t diy-diagnosis .
   docker run -p 8000:8000 --env-file .env diy-diagnosis
   ```
5. Open your browser:
   - **Web Interface**: http://localhost:8000 (Chat interface with timing display)
   - **API Documentation**: http://localhost:8000/docs

### Run Locally (Development)

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

4. Add your OpenAI API key to `.env`

5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open your browser:
   - **Web Interface**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## Web Interface

The application includes a beautiful chat-based web interface with real-time performance monitoring.

### Features

- **Drag & Drop Upload** - Drag images directly into the chat or click to upload
- **Chat Interface** - Natural conversation flow for asking follow-up questions
- **Performance Metrics** - Click the ℹ️ Details button to see:
  - **Total Time** - Complete request duration
  - **Image Processing** - Validation and preprocessing time
  - **Cache Lookup** - Time spent checking cache
  - **OpenAI API Call** - GPT-4o Vision processing time
  - **Material Normalization** - Brand/SKU removal time
  - **OpenAI Cost Estimate** - Approximate cost per request ($0.015-0.025 typical)
- **Cache Status** - Shows if result was cached (0.3s) or fresh (2-3s)
- **Session Management** - Automatic session tracking for multi-turn conversations
- **Clickable Suggestions** - Click suggested follow-up questions to ask them instantly
- **Responsive Design** - Works on desktop, tablet, and mobile

### Usage

1. Open http://localhost:8000 in your browser
2. Upload a photo of the broken item (drag & drop or click)
3. Review the diagnosis, materials, and repair steps
4. Click **ℹ️ Details** to see performance metrics and OpenAI costs
5. Ask follow-up questions in the chat
6. Click "New Diagnosis" to start over

### Performance Metrics

Each response shows a compact summary with an expandable details panel:

**Compact View:**
```
ℹ️ Details   2.45s • New
```

**Expanded Details Panel (click ℹ️):**

**⏱️ Performance Metrics**
- Total Time: 2.45s
- Image Processing: 0.18s
- Cache Lookup: 0.05s
- OpenAI API Call: 2.15s
- Material Normalization: 0.07s

**💰 OpenAI Cost Estimate**
- Model: GPT-4o Vision
- Estimated Cost: ~$0.0180
- Input Tokens: 1200 (~$0.0030)
- Output Tokens: 1000 (~$0.0150)

**📦 Cache Status**
- Source: New diagnosis - API cost incurred

**Understanding the Metrics:**
- **Cached requests**: ~0.3s, $0.00 API cost
- **Fresh diagnosis**: ~2.5s, ~$0.018 API cost
- **Follow-up questions**: ~1.8s, ~$0.009 API cost
- Cache dramatically reduces both time and cost!

## API Usage

### Diagnose an Item

**Endpoint:** `POST /diagnose`

**Request** (multipart/form-data):
```bash
curl -X POST "http://localhost:8000/diagnose" \
  -F "image=@broken_toilet.jpg"
```

**Response** (JSON):
```json
{
  "diagnosis": "worn toilet flapper valve",
  "confidence": 0.92,
  "issue_type": "plumbing",
  "materials": [
    {
      "name": "rubber flapper valve",
      "category": "plumbing",
      "search_query": "toilet flapper valve replacement"
    }
  ],
  "tools_required": ["adjustable wrench", "bucket"],
  "repair_steps": [
    {
      "step": 1,
      "title": "Turn off water supply",
      "instruction": "Locate the shut-off valve behind the toilet and turn clockwise",
      "safety_tip": "Place towels around the base to catch any water"
    }
  ],
  "warnings": ["Ensure water is completely off before proceeding"],
  "followup_questions": [
    "Do you have the necessary tools?",
    "Is the water supply accessible?"
  ],
  "session_id": "abc-123-def-456"
}
```

### Follow-up Question

**Request**:
```bash
curl -X POST "http://localhost:8000/diagnose" \
  -F "session_id=abc-123-def-456" \
  -F "question=What tools do I need?"
```

**Response**:
Returns updated diagnosis with additional details merged in.

### Health Check

**Endpoint:** `GET /health`

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "cache_stats": {
    "exact_hits": 45,
    "perceptual_hits": 12,
    "misses": 103,
    "total_requests": 160,
    "hit_rate": 35.63,
    "exact_cache_size": 87,
    "perceptual_cache_size": 95
  },
  "active_sessions": 23
}
```

## Configuration

All configuration is done via environment variables. See `.env.example` for all available options.

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model to use |
| `MAX_IMAGE_SIZE_MB` | `10` | Maximum upload size |
| `CACHE_TTL_SECONDS` | `3600` | Cache expiration time |
| `SESSION_TTL_MINUTES` | `30` | Session expiration time |

## Architecture

### Components

- **FastAPI** - Async API framework with automatic OpenAPI docs
- **GPT-4o Vision** - AI-powered image analysis
- **Image Processor** - Quality validation and preprocessing
- **Material Normalizer** - Removes brands/SKUs/URLs
- **Session Manager** - Thread-safe multi-turn conversations
- **Cache Manager** - Two-level caching (exact + perceptual)

### Request Flow

```
1. Upload image
   ↓
2. Validate image (size, format, quality)
   ↓
3. Check exact cache (SHA256)
   ↓
4. Check perceptual cache (similar images)
   ↓
5. Call GPT-4o Vision
   ↓
6. Normalize materials (remove brands)
   ↓
7. Cache result
   ↓
8. Update session
   ↓
9. Return diagnosis
```

### Image Quality Gate

Before calling GPT-4o, images are validated:

- **Format**: JPEG, PNG, WebP only
- **Size**: 50KB - 10MB
- **Dimensions**: 200x200px minimum
- **Blur detection**: Laplacian variance > 100
- **Brightness**: Mean pixel 40-240
- **Contrast**: Standard deviation > 20

Images that fail validation return an "Image unclear" response without consuming API credits.

### Caching Strategy

**Level 1 - Exact Match:**
- SHA256 hash of image + question
- 1-hour TTL
- Instant hits for identical requests

**Level 2 - Perceptual Hash:**
- Finds similar images (even if slightly different)
- 24-hour TTL
- Reduces redundant API calls

## Testing

### Run Tests

```bash
pytest tests/
```

### Test Coverage

```bash
pytest --cov=app tests/
```

### Manual Testing

Test with sample images:

```bash
# Good quality image
curl -X POST "http://localhost:8000/diagnose" \
  -F "image=@tests/fixtures/sample_images/good_quality.jpg"

# Blurry image (should be rejected)
curl -X POST "http://localhost:8000/diagnose" \
  -F "image=@tests/fixtures/sample_images/blurry.jpg"
```

## Troubleshooting

### "Image unclear" responses

**Problem**: Getting too many "Image unclear" responses

**Solutions**:
- Ensure good lighting
- Focus clearly on the damaged area
- Hold camera steady to avoid blur
- Minimum resolution: 200x200px
- Avoid extreme shadows or highlights

### Slow response times

**Problem**: API taking > 2.5 seconds

**Solutions**:
- Check cache hit rate at `/health`
- Reduce `OPENAI_MAX_TOKENS` in `.env`
- Use smaller images (< 1MB)
- Ensure adequate server resources

### Brand names in materials

**Problem**: Response includes brand names despite filtering

**Solutions**:
- Material normalizer should catch most brands
- If you find a brand that slips through, add it to `BRAND_PATTERNS` in [app/utils/material_normalizer.py](app/utils/material_normalizer.py)
- Open an issue with the brand name

### OpenAI API errors

**Problem**: 429 Rate Limit or 500 Server Error

**Solutions**:
- Check your OpenAI API quota
- Increase `MAX_RETRIES` in `.env`
- Add exponential backoff (already implemented)
- Check OpenAI status page

### Docker build failures

**Problem**: Docker build fails

**Solutions**:
- Ensure you have latest Docker version
- Check system dependencies for opencv
- On Windows, use WSL2 backend
- Try: `docker build --no-cache -t diy-diagnosis .`

### Session not found

**Problem**: "Session not found or expired"

**Solutions**:
- Sessions expire after 30 minutes (configurable)
- Save session_id from initial diagnosis
- Include session_id in follow-up requests
- Increase `SESSION_TTL_MINUTES` if needed

## Performance

### Benchmarks

- **First request**: < 2.5s (with GPT call)
- **Cached request**: < 0.5s (cache hit)
- **Image preprocessing**: < 0.2s
- **Material normalization**: < 0.01s

### Optimization Tips

1. **Enable caching**: Use cache to avoid redundant API calls
2. **Compress images**: Smaller images = faster uploads and processing
3. **Use exact duplicates**: Identical images hit exact cache
4. **Warm up cache**: Pre-diagnose common items
5. **Scale horizontally**: Run multiple instances behind load balancer

## Security

### Best Practices

- Store `OPENAI_API_KEY` in environment variables only
- Never commit `.env` file to version control
- Use non-root user in Docker container
- Enable CORS only for trusted origins
- Rate limit endpoint in production
- Monitor API costs

### API Key Protection

The API key is:
- Never logged or exposed in error messages
- Not included in response data
- Only accessible to the FastAPI app
- Loaded from environment variables

## Production Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Environment Variables

For production, set these environment variables:

```bash
OPENAI_API_KEY=sk-prod-key-here
ALLOWED_ORIGINS=https://yourdomain.com
UVICORN_WORKERS=4
SESSION_TTL_MINUTES=60
```

### Monitoring

Monitor these metrics:

- Cache hit rate (target: > 70%)
- Average response time (target: < 2.5s)
- Active sessions count
- API error rate
- OpenAI API costs

## Known Limitations

1. **No database** - Sessions and cache are in-memory only
2. **No authentication** - Open API (add auth layer for production)
3. **No rate limiting** - Add rate limiting in production
4. **No video support** - Images only (video planned for future)
5. **English only** - No multi-language support yet

## Future Enhancements

- [ ] Database persistence (PostgreSQL)
- [ ] User authentication and accounts
- [ ] Video analysis support
- [ ] Cost estimation for materials
- [ ] Multi-language support
- [ ] Mobile app companion
- [ ] Community feedback system
- [ ] Advanced analytics dashboard

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or feature requests:

- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## Acknowledgments

- Built with FastAPI and GPT-4o Vision
- Uses OpenCV for image quality detection
- Perceptual hashing via imagehash library
