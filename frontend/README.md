# Frontend - DIY Repair Assistant Chat Interface

Modern, responsive chat interface for the DIY Repair Diagnosis API.

## Features

- **Drag & Drop Upload** - Upload images by dragging them into the chat
- **Real-time Performance Metrics** - See timing breakdown for each request
- **Cache Status Indicators** - Visual badges show cache hits/misses
- **Session Management** - Automatic session tracking for multi-turn conversations
- **Responsive Design** - Works on all devices
- **Clickable Suggestions** - Click follow-up questions to ask them

## Files

- `index.html` - Main HTML structure
- `style.css` - Styling and animations
- `script.js` - Frontend logic and API communication

## Configuration

The frontend connects to the API at `http://localhost:8000` by default.

To change the API URL, edit `script.js`:

```javascript
const API_BASE_URL = 'http://your-api-url:8000';
```

## Performance Display

The interface shows a compact info button that expands to show detailed metrics:

### Compact View
Every response shows: `ℹ️ Details  2.45s • New`

Click the **ℹ️ Details** button to expand the panel.

### Expanded Details Panel

**⏱️ Performance Metrics**
- Total Time - Complete request duration
- Image Processing - Validation and preprocessing
- Cache Lookup - Time checking cache
- OpenAI API Call - GPT-4o Vision processing time
- Material Normalization - Brand/SKU removal

**💰 OpenAI Cost Estimate**
- Model name (GPT-4o Vision)
- Estimated cost per request
- Token breakdown (input/output)
- Cost per token type

**📦 Cache Status**
- Whether result was cached or fresh
- Cost implications (cached = $0.00)

### Typical Costs
- **Fresh diagnosis**: ~$0.018 (1200 input + 1000 output tokens)
- **Follow-up question**: ~$0.009 (500 input + 400 output tokens)
- **Cached result**: $0.00 (no API call)

## Development

The frontend is pure HTML/CSS/JavaScript (no build step required).

### Testing Locally

1. Start the backend API
2. Open `index.html` in a browser, or
3. Visit http://localhost:8000 (served by FastAPI)

### Customization

**Change Colors:**
Edit CSS variables in `style.css`:
```css
:root {
    --primary: #2563eb;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}
```

**Modify Layout:**
Update classes in `index.html` and corresponding styles in `style.css`.

**Add Features:**
Extend `script.js` functions and API calls.

## Browser Support

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- Mobile browsers: ✅ Responsive design

## API Integration

The frontend communicates with these endpoints:

- `POST /diagnose` - Upload image and get diagnosis
- `POST /diagnose` - Send follow-up questions (with session_id)
- `GET /health` - Health check (not used in UI)

### Request Format

**Initial Diagnosis:**
```javascript
const formData = new FormData();
formData.append('image', file);
```

**Follow-up Question:**
```javascript
const formData = new FormData();
formData.append('session_id', currentSessionId);
formData.append('question', question);
```

### Response Format

See [API Documentation](http://localhost:8000/docs) for complete response schemas.

## Performance

The interface is optimized for:
- Fast initial load (no frameworks)
- Smooth animations (CSS transitions)
- Efficient DOM updates
- Real-time status updates

## Accessibility

- Keyboard navigation supported
- Screen reader friendly
- High contrast mode compatible
- Focus indicators for interactive elements
