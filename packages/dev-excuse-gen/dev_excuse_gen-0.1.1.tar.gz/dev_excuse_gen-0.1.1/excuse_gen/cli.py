import random
import argparse

CAUSES =[
    "a race condition",
    "undefined behavior in the dependency",
    "a subtle state mutation",
    "an unhandled edge case",
    "non-deterministic ordering"
]

TRIGGERS=[
    "only after the cache warmed up",
    "under production load",
    "when retries overlap",
    "during async cleanup",
    "after a silent fallback"
]

ACTIONS=[
    "masked it in staging",
    "made it impossible to reproduce locally",
    "bypassed the alerting",
    "delayed detection",
    "looked harmless at first"
]

CONFIDENCE=["low","medium","high"]

def generate_excuse(context):
    cause=random.choice(CAUSES)
    trigger=random.choice(TRIGGERS)
    action=random.choice(ACTIONS)
    confidence=random.choice(CONFIDENCE)
    return (
        f"Root Cause identified.\n"
        f"{cause.capitalize()} surfaced {trigger} and {action}."
        f"Fix is trivial. Confidence is {confidence}"
    )

def main():
    parser=argparse.ArgumentParser(description="Generate realisitic programming excuses.")
    parser.add_argument("--context", default="general")
    args = parser.parse_args()

    print(generate_excuse(args.context))

# if __name__=="__main__":
#     main()
