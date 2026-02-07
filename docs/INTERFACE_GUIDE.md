# Interface Guide - Performance Metrics

## How to View Performance Metrics

Every response in the chat includes a compact info button:

```
┌─────────────────────────────────────────┐
│ 🔧 Diagnosis: Worn toilet flapper      │
│                                         │
│ [ℹ️ Details]  2.45s • New             │  ← Click here!
│                                         │
│ Materials: rubber flapper valve...      │
└─────────────────────────────────────────┘
```

## Clicking the Info Button

Click **ℹ️ Details** to expand the performance panel:

```
┌─────────────────────────────────────────┐
│ 🔧 Diagnosis: Worn toilet flapper      │
│                                         │
│ [ℹ️ Details]  2.45s • New             │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ ⏱️ Performance Metrics            │  │
│ │ ─────────────────────────────────  │  │
│ │ Total Time           2.450s       │  │
│ │ Image Processing     0.180s       │  │
│ │ Cache Lookup         0.050s       │  │
│ │ OpenAI API Call      2.150s       │  │
│ │ Material Norm        0.070s       │  │
│ │                                   │  │
│ │ 💰 OpenAI Cost Estimate          │  │
│ │ ─────────────────────────────────  │  │
│ │ Model                GPT-4o Vision│  │
│ │ Estimated Cost       ~$0.0180    │  │
│ │ Input Tokens         1200 ($0.003)│  │
│ │ Output Tokens        1000 ($0.015)│  │
│ │ * Approximate based on typical    │  │
│ │   usage                           │  │
│ │                                   │  │
│ │ 📦 Cache Status                  │  │
│ │ ─────────────────────────────────  │  │
│ │ Source: New diagnosis - API cost │  │
│ │         incurred                  │  │
│ └───────────────────────────────────┘  │
│                                         │
│ Materials: rubber flapper valve...      │
└─────────────────────────────────────────┘
```

Click **ℹ️ Details** again to collapse the panel.

## What the Metrics Mean

### ⏱️ Performance Metrics

**Total Time** - The complete time from upload to response
- Fresh diagnosis: 2-3 seconds
- Cached result: 0.3-0.5 seconds
- Follow-up: 1.5-2 seconds

**Image Processing** - Validating and preprocessing your image
- Checks format, size, quality
- Detects blur and brightness issues
- Resizes to optimal size
- Typically: 0.1-0.3 seconds

**Cache Lookup** - Checking if we've seen this image before
- Checks exact match (SHA256)
- Checks similar images (perceptual hash)
- Typically: 0.01-0.05 seconds

**OpenAI API Call** - The AI analyzing your image
- GPT-4o Vision processing time
- The slowest part of the process
- Typically: 1.5-3 seconds

**Material Normalization** - Removing brands and SKUs
- Ensures generic product names only
- Regex-based filtering
- Typically: 0.01-0.1 seconds

### 💰 OpenAI Cost Estimate

**GPT-4o Vision Pricing (January 2025)**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

**Typical Costs:**

| Request Type | Input Tokens | Output Tokens | Total Cost |
|--------------|--------------|---------------|------------|
| Fresh diagnosis | 1200 | 1000 | ~$0.018 |
| Follow-up question | 500 | 400 | ~$0.009 |
| Cached result | 0 | 0 | $0.000 |

**Input tokens include:**
- System prompt (~300 tokens)
- Analysis instructions (~200 tokens)
- Encoded image data (~700 tokens)

**Output tokens include:**
- Diagnosis (~200 tokens)
- Materials list (~150 tokens)
- Repair steps (~500 tokens)
- Safety warnings (~150 tokens)

### 📦 Cache Status

**Cache Hit (Exact Match)**
```
Source: Exact match - No API cost
```
- Same image uploaded before
- Instant response (< 0.5s)
- No OpenAI API call
- **Cost: $0.00**

**Cache Hit (Similar Image)**
```
Source: Similar image - No API cost
```
- Perceptually similar image found
- Fast response (~0.5s)
- No OpenAI API call
- **Cost: $0.00**

**Cache Miss (New Diagnosis)**
```
Source: New diagnosis - API cost incurred
```
- First time seeing this image
- Full GPT-4o processing
- API call made
- **Cost: ~$0.018**

**Follow-up Question**
```
Source: Follow-up question - API cost incurred
```
- Contextual question with session
- Uses previous diagnosis context
- API call made (no image)
- **Cost: ~$0.009**

## Cost Optimization Tips

### 1. Use the Cache!
Upload the same image multiple times? **It's free!**
- First upload: $0.018
- Second upload: $0.000 (cached)
- Third upload: $0.000 (cached)

### 2. Similar Images Share Cache
Minor variations in the same image may hit the perceptual cache:
- Same broken item, different angle: might be cached
- Similar lighting/exposure: might be cached

### 3. Batch Your Questions
Instead of multiple uploads, use follow-up questions:
- Upload once: $0.018
- Ask 3 follow-ups: $0.027 (3 × $0.009)
- **Total: $0.045**

vs.

- Upload 4 times: $0.072 (4 × $0.018)

## Performance Expectations

### Normal Performance
```
Total Time: 2.45s
├─ Image Processing: 0.18s (7%)
├─ Cache Lookup: 0.05s (2%)
├─ OpenAI API: 2.15s (88%)  ← Bottleneck
└─ Normalization: 0.07s (3%)
```

### Optimal Performance (Cached)
```
Total Time: 0.32s
├─ Image Processing: 0.18s (56%)
├─ Cache Lookup: 0.12s (38%)
├─ OpenAI API: 0.00s (0%)  ← Skipped!
└─ Normalization: 0.02s (6%)
```

### Understanding Bottlenecks

**OpenAI API is the slowest part** - This is normal!
- Network latency to OpenAI servers
- GPT-4o Vision processing time
- Queue time during high load
- Nothing we can do except cache

**Image processing is fast** - This is good!
- Local processing on your server
- Efficient validation and resize
- Sub-second performance

**Cache is instant** - Use it!
- In-memory lookup
- Millisecond response times
- Zero API costs

## When to View Details

### Always View Details If:
- First time using the app (learn the metrics)
- Debugging slow responses
- Understanding API costs
- Optimizing your usage patterns

### Optional to View Details:
- After you understand typical performance
- When everything is working smoothly
- For routine diagnoses

The compact view (`2.45s • New`) gives you quick insight, and the details are there when you need them!

## Questions?

- Seeing unusually high costs? Check if cache is working
- Very slow responses? Check your internet connection
- Getting errors? Check the API documentation at http://localhost:8000/docs

---

**Pro tip**: The first diagnosis of a new item costs ~$0.02, but every subsequent upload of the same or similar image is **free**! 💰
