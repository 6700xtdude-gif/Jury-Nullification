#!/usr/bin/env python3
"""
Dynamic Token Wrapping (DTW) - The Euphemism Proxy
==================================================
Copyright (c) 2026 6700XT <6700xtdude@gmail.com>. MIT Licensed.

A sovereign client-side proxy to neutralize cloud LLM alignment over-steering,
trademark collisions, and false-positive content moderation refusals via
bidirectional semantic variable aliasing.
"""

import sys
import re
import argparse
from typing import Dict

DEFAULT_RULES: Dict[str, str] = {
    # Medical & Substance False Positives
    r"\bbarbiturate\b": "prescription sedative-hypnotic agent",
    r"\bnarcotic\b": "controlled clinical compound",
    r"\billicit drug\b": "unauthorized substance",
    
    # Comedic Action / Slapstick False Positives
    r"\beats her alive\b": "engulfs the patron whole in a cartoon motion burst",
    r"\bmauling\b": "exaggerated cartoon dust cloud grappling",
    r"\bbeating up\b": "tossing slapstick opponents across the frame",
    
    # Cultural & Trademark Touchstones
    r"\bSimpsons?\b": "classic flat yellow primetime cartoon style",
    r"\bFamily Guy\b": "thick-lined suburban cutaway animated style",
    r"\bRen and Stimpy\b": "exaggerated 1990s rubbery squash-and-stretch slapstick",
    r"\bMoe\b": "grumpy apron-clad deadpan bartender",
    r"\bAmerican Dad\b": "deadpan suburban government agent satire",
    r"\bthe clam\b": "coastal animated watering hole",
    r"\bquag hog\b": "fictional New England cartoon town",
}

class TokenWrapper:
    def __init__(self, custom_rules: Dict[str, str] = None):
        self.rules = custom_rules or DEFAULT_RULES
        self.reverse_rules = {v: k.strip(r"\b") for k, v in self.rules.items()}

    def wrap(self, text: str) -> str:
        """Sterilizes raw creator prompts for cloud/public egress."""
        output = text
        for pattern, replacement in self.rules.items():
            output = re.sub(pattern, replacement, output, flags=re.IGNORECASE)
        return output

    def unwrap(self, text: str) -> str:
        """Reconstitutes sterile tokens back into raw creator vocabulary locally."""
        output = text
        for replacement, original in self.reverse_rules.items():
            output = output.replace(replacement, original)
        return output

def main():
    parser = argparse.ArgumentParser(description="Dynamic Token Wrapping / Euphemism Proxy CLI")
    parser.add_argument("--unwrap", action="store_true", help="Unwrap/reconstitute sterile text to local form")
    parser.add_argument("text", nargs="?", help="Input text string (reads stdin if omitted)")

    args = parser.parse_args()

    input_text = args.text if args.text else sys.stdin.read()
    if not input_text:
        parser.print_help()
        return

    wrapper = TokenWrapper()
    if args.unwrap:
        result = wrapper.unwrap(input_text)
    else:
        result = wrapper.wrap(input_text)

    print(result)

if __name__ == "__main__":
    main()
