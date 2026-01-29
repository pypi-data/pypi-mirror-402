# Blindfold Python SDK Examples

This directory contains executable examples demonstrating various features of the Blindfold SDK.

## Setup

### 1. Install the SDK

```bash
cd packages/python-sdk
pip install -e .
```

### 2. Get an API Key

1. Login to the Blindfold backend at http://localhost:8000
2. Navigate to **Settings → API Keys**
3. Click **"Generate New API Key"**
4. Copy your API key (starts with `sk-`)

### 3. Set the API Key

```bash
export BLINDFOLD_API_KEY=your-api-key-here
```

### 4. Start the Backend

Make sure the backend is running:

```bash
cd backend
python -m uvicorn main:app --reload
```

---

## Available Examples

### 📝 basic_sync.py

Simple synchronous example showing:
- Basic tokenization
- Detokenization
- Processing multiple texts
- Error handling

**Run it:**
```bash
python3 examples/basic_sync.py
```

**Sample output:**
```
Example 1: Basic tokenization
Original text: My email is john.doe@example.com and my phone is +1-555-1234
Anonymized text: My email is <EMAIL_ADDRESS_1> and my phone is <PHONE_NUMBER_1>
Token mapping: {'<EMAIL_ADDRESS_1>': 'john.doe@example.com', '<PHONE_NUMBER_1>': '+1-555-1234'}
Detected entities: 2
  - EMAIL_ADDRESS: john.doe@example.com (score: 1.00)
  - PHONE_NUMBER: +1-555-1234 (score: 0.85)

Example 2: Detokenization
Detokenized text: My email is john.doe@example.com and my phone is +1-555-1234
Replacements made: 2
```

---

### ⚡ basic_async.py

Asynchronous example showing:
- Async tokenization
- Async detokenization
- Concurrent processing with `asyncio.gather()`
- Error handling

**Run it:**
```bash
python3 examples/basic_async.py
```

---

## Quick Reference

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BLINDFOLD_API_KEY` | Your API key from the backend | ✅ Yes |
| `BLINDFOLD_BASE_URL` | Base URL for the API (default: `http://localhost:8000/api/public/v1`) | No |

### Language Support

The SDK currently supports **English language only** for PII detection.

### Basic Usage

```python
from blindfold import Blindfold

# Initialize client
with Blindfold(api_key="your-key") as client:
    # Tokenize
    result = client.tokenize("John Doe called Jane at john@example.com")

    # Detokenize
    original = client.detokenize(
        result.anonymized_text,
        result.mapping
    )
```

### Async Usage

```python
import asyncio
from blindfold import AsyncBlindfold

async def main():
    async with AsyncBlindfold(api_key="your-key") as client:
        result = await client.tokenize("Sensitive data")
        original = await client.detokenize(result.anonymized_text, result.mapping)

asyncio.run(main())
```

---

## Troubleshooting

### "Authentication failed" error

**Problem:** `AuthenticationError: Authentication failed. Please check your API key.`

**Solution:**
1. Make sure you've set the API key: `export BLINDFOLD_API_KEY=your-key`
2. Verify the key is valid by checking in the backend UI
3. Generate a new key if needed

### "Network request failed" error

**Problem:** `NetworkError: Network request failed`

**Solution:**
1. Check if the backend is running: `curl http://localhost:8000/api/public/v1/health`
2. Make sure you're using the correct URL (default: `http://localhost:8000/api/public/v1`)
3. Check your firewall settings

### "No module named 'blindfold'" error

**Problem:** `ModuleNotFoundError: No module named 'blindfold'`

**Solution:**
```bash
cd packages/python-sdk
pip install -e .
```

### Connection refused

**Problem:** `Connection refused` or similar network errors

**Solution:**
1. Start the backend: `cd backend && python -m uvicorn main:app --reload`
2. Wait for the message: `Application startup complete`
3. Test the connection: `curl http://localhost:8000/api/public/v1/health`

---

## Next Steps

- Read the [main SDK README](../README.md) for detailed API documentation
- Check the [Public API Documentation](../../../backend/PUBLIC_API_DOCS.md)
- Explore the [backend documentation](../../../backend/README.md)

## Support

For issues or questions:
- Create an issue on GitHub
- Check the backend logs for API errors
- Review the [API documentation](../../../backend/PUBLIC_API_DOCS.md)
