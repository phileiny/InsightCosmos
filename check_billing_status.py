import asyncio
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

async def make_request(index):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Use a very short prompt to minimize token usage and latency
        response = await model.generate_content_async("Hi", generation_config={"max_output_tokens": 1})
        return True, index, None
    except Exception as e:
        return False, index, str(e)

async def main():
    print("🚀 Starting Billing Status Check...")
    print("-----------------------------------")
    print(f"Testing API Key: {api_key[:5]}...{api_key[-5:]}")
    print("Strategy: Sending 20 concurrent requests to 'gemini-1.5-flash'.")
    print("Reason: Free Tier limit is ~15 RPM. Paid Tier is ~2000 RPM.")
    print("-----------------------------------")

    start_time = time.time()
    
    # Create 20 concurrent tasks
    tasks = [make_request(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time

    success_count = sum(1 for r in results if r[0])
    fail_count = sum(1 for r in results if not r[0])

    print(f"\n📊 Results:")
    print(f"  Total Requests: 20")
    print(f"  Duration:       {duration:.2f} seconds")
    print(f"  Success:        {success_count}")
    print(f"  Failed:         {fail_count}")

    print("\n🔍 Analysis:")
    if fail_count > 0:
        print("  ⚠️  Failures detected!")
        # Check if errors are 429
        rate_limit_errors = [r[2] for r in results if not r[0] and "429" in str(r[2])]
        if rate_limit_errors:
            print(f"  🔴  Confirmed 429 (Rate Limit) errors: {len(rate_limit_errors)}")
            print("  👉  CONCLUSION: You are likely still on the **FREE TIER**.")
            print("      (Or you hit the daily limit, or the billing update hasn't propagated yet.)")
        else:
            print("  ⚠️  Errors were not 429s. Check logs below.")
            for r in results:
                if not r[0]:
                    print(f"    - Request {r[1]}: {r[2]}")
    else:
        print("  ✅  All 20 requests succeeded in {:.2f} seconds.".format(duration))
        if duration < 2.0:
            # If it was super fast and all succeeded, it's a very strong signal
            print("  👉  CONCLUSION: You are likely on the **PAID TIER** (Pay-as-you-go).")
            print("      (Free tier would almost certainly fail > 15 requests in < 2 seconds)")
        else:
            print("  👉  CONCLUSION: Likely **PAID TIER**, but network was slow.")

if __name__ == "__main__":
    asyncio.run(main())
