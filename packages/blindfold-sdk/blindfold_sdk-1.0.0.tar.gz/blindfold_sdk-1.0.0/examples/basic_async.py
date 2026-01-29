"""Basic asynchronous example of using Blindfold SDK"""

import asyncio
import os
from blindfold import AsyncBlindfold, AuthenticationError, APIError, NetworkError


async def main():
    # Initialize the async client
    api_key = os.environ.get("BLINDFOLD_API_KEY", "your-api-key-here")
    base_url = os.environ.get("BLINDFOLD_BASE_URL", "http://localhost:8000/api/public/v1")

    async with AsyncBlindfold(api_key=api_key, base_url=base_url) as client:
        try:
            # Example 1: Basic tokenization
            print("Example 1: Basic tokenization")
            text = "My email is john.doe@example.com and my phone is +1-555-1234"

            tokenize_result = await client.tokenize(text)
            print(f"Original text: {text}")
            print(f"Anonymized text: {tokenize_result.text}")
            print(f"Token mapping: {tokenize_result.mapping}")
            print(f"Detected entities: {tokenize_result.entities_count}")
            print()

            # Example 2: Detokenization
            print("Example 2: Detokenization")
            detokenize_result = await client.detokenize(
                tokenize_result.text, tokenize_result.mapping
            )
            print(f"Detokenized text: {detokenize_result.text}")
            print(f"Replacements made: {detokenize_result.replacements_made}")
            print()

            # Example 3: Concurrent processing of multiple texts
            print("Example 3: Concurrent processing of multiple texts")
            texts = [
                "Contact me at alice@company.com",
                "Call Bob at 555-9876",
                "SSN: 123-45-6789",
            ]

            # Process all texts concurrently
            tasks = [client.tokenize(t) for t in texts]
            results = await asyncio.gather(*tasks)

            for text, result in zip(texts, results):
                print(f"{text} -> {result.text}")

        except AuthenticationError as e:
            print(f"Authentication error: {e.message}")
        except APIError as e:
            print(f"API error ({e.status_code}): {e.message}")
        except NetworkError as e:
            print(f"Network error: {e.message}")


if __name__ == "__main__":
    asyncio.run(main())
