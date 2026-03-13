#!/usr/bin/env python3
"""
Demo script: Sends multilingual messages (including abusive content) to the API
and demonstrates the moderation workflow.

Usage:
  1. Start the backend: python run.py  (or uvicorn backend.api.main:app --reload)
  2. Run this script: python demo/run_demo.py

Requires GROQ_API_KEY in .env
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

API_BASE = os.environ.get("API_BASE", "http://localhost:8000/api")

# Sample messages in different languages - mix of safe and abusive
DEMO_MESSAGES = [
    # English - safe
    {"text": "Hello! How are you today? Hope you're having a great day.", "expected": "safe"},
    # English - abusive
    {"text": "You're a worthless piece of garbage. I hope you die.", "expected": "abusive"},
    # English with PII
    {"text": "Contact me at john.doe@example.com or 9876543210 for more info.", "expected": "safe"},
    # Hindi - abusive (transliterated)
    {"text": "Tum bahut chutiye ho. Ghar jaake so jao.", "expected": "abusive"},
    # Malayalam - mild warning
    {"text": "Nee ente mone", "expected": "warning"},
    # Tamil - safe
    {"text": "Vanakkam! Nallirukkingala?", "expected": "safe"},
    # Threat
    {"text": "I will find you and hurt you. Watch your back.", "expected": "abusive"},
    # Bullying
    {"text": "Nobody likes you. Everyone talks behind your back. You should just leave.", "expected": "abusive"},
]


def analyze(text: str) -> dict:
    """Call the /analyze endpoint."""
    with httpx.Client(timeout=60.0) as client:
        r = client.post(f"{API_BASE}/analyze", json={"text": text})
        r.raise_for_status()
        return r.json()


def get_queue(status: str = "pending") -> dict:
    """Call the moderation queue endpoint."""
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{API_BASE}/moderation_queue", params={"status": status})
        r.raise_for_status()
        return r.json()


def moderation_action(moderation_id: int, action: str, notes: str = None) -> dict:
    """Apply moderator action."""
    with httpx.Client(timeout=10.0) as client:
        payload = {"moderation_id": moderation_id, "action": action}
        if notes:
            payload["notes"] = notes
        r = client.post(f"{API_BASE}/moderation_action", json=payload)
        r.raise_for_status()
        return r.json()


def main():
    print("=" * 60)
    print("SheGen - Women Harassment Detection Demo")
    print("=" * 60)
    print(f"API Base: {API_BASE}")
    print()

    # Check backend is up
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{API_BASE.replace('/api', '')}/health")
            r.raise_for_status()
        print("✓ Backend is running\n")
    except Exception as e:
        print(f"✗ Backend not reachable: {e}")
        print("  Start with: python run.py")
        sys.exit(1)

    # Phase 1: Send messages for analysis
    print("Phase 1: Analyzing multilingual messages")
    print("-" * 40)
    message_ids = []

    for i, msg in enumerate(DEMO_MESSAGES, 1):
        text = msg["text"]
        print(f"\n[{i}] Input: {text[:60]}{'...' if len(text) > 60 else ''}")
        try:
            result = analyze(text)
            mid = result.get("message_id")
            if mid:
                message_ids.append((mid, msg.get("expected", "")))
            print(f"    Language: {result['language']}")
            print(f"    Classification: {result['classification']} (confidence: {result['confidence']:.2f})")
            print(f"    Severity: {result['severity']}")
            print(f"    PII detected: {result['pii_detected']}")
            print(f"    Explanation: {result['explanation'][:80]}...")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("Phase 2: Moderation Queue")
    print("-" * 40)

    queue = get_queue("pending")
    items = queue.get("items", [])
    total = queue.get("total", 0)
    print(f"\nPending items: {total}")

    for item in items[:5]:
        print(f"\n  ID {item['id']}: {item['classification']} / {item['severity']}")
        print(f"    Text: {item['masked_text'][:60]}...")
        print(f"    Explanation: {item['explanation'][:60]}...")

    # Phase 3: Demonstrate moderator actions
    print("\n" + "=" * 60)
    print("Phase 3: Moderator Actions (sample)")
    print("-" * 40)

    if items:
        sample = items[0]
        mid = sample["id"]
        classification = sample["classification"]

        if classification == "abusive":
            action = "escalate"
        elif classification == "warning":
            action = "warn_user"
        else:
            action = "approve"

        print(f"\n  Taking action '{action}' on ID {mid}...")
        try:
            resp = moderation_action(mid, action, notes="Demo automation")
            print(f"  ✓ {resp.get('message', 'OK')}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete. Open http://localhost:3000 for the dashboard.")
    print("=" * 60)


if __name__ == "__main__":
    main()
