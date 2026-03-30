#!/usr/bin/env python3
"""
Script to update all translation files using Español.json as base.
Merges missing keys from English.json as fallback placeholders.
"""

import json
import os
from pathlib import Path

def load_json(filepath):
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save data to a JSON file with proper formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def merge_translations(base, target, fallback):
    """
    Recursively merge translations.
    - base: Spanish structure (defines the keys)
    - target: Current language translations
    - fallback: English translations (used when key is missing)
    Returns merged dict.
    """
    result = {}
    
    for key, base_value in base.items():
        if key in target:
            target_value = target[key]
            if isinstance(base_value, dict) and isinstance(target_value, dict):
                # Recursively merge nested dicts
                fallback_value = fallback.get(key, {}) if isinstance(fallback.get(key), dict) else {}
                result[key] = merge_translations(base_value, target_value, fallback_value)
            else:
                # Keep existing translation
                result[key] = target_value
        elif key in fallback:
            fallback_value = fallback[key]
            if isinstance(base_value, dict) and isinstance(fallback_value, dict):
                # Use fallback structure
                result[key] = fallback_value
            else:
                # Use fallback value
                result[key] = fallback_value
        else:
            # Use base value (Spanish) as last resort
            result[key] = base_value
    
    return result

def update_language_file(filepath, base_translations, fallback_translations):
    """Update a single language file with missing translations."""
    try:
        lang_data = load_json(filepath)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"  Warning: Could not load {filepath}, skipping")
        return False
    
    if 'translations' not in lang_data:
        print(f"  Warning: No 'translations' key in {filepath}, skipping")
        return False
    
    # Merge translations
    original_translations = lang_data['translations']
    merged_translations = merge_translations(
        base_translations,
        original_translations,
        fallback_translations
    )
    
    # Update the language data
    lang_data['translations'] = merged_translations
    
    # Save the updated file
    save_json(filepath, lang_data)
    return True

def main():
    """Main function to update all translation files."""
    # Paths
    translations_dir = Path(__file__).parent.parent / 'resources' / 'translations'
    spanish_file = translations_dir / 'Español.json'
    english_file = translations_dir / 'English.json'
    
    print(f"Translations directory: {translations_dir}")
    
    # Load base (Spanish) and fallback (English) translations
    spanish_data = load_json(spanish_file)
    english_data = load_json(english_file)
    
    base_translations = spanish_data['translations']
    fallback_translations = english_data['translations']
    
    print(f"Loaded Spanish base with {count_keys(base_translations)} keys")
    print(f"Loaded English fallback with {count_keys(fallback_translations)} keys")
    print()
    
    # Update all language files
    updated_count = 0
    skipped_count = 0
    
    for filepath in translations_dir.glob('*.json'):
        filename = filepath.name
        
        # Skip Spanish (it's our base) and non-language files
        if filename in ('Español.json', '__init__.py'):
            continue
        
        print(f"Updating {filename}...", end=' ')
        
        if update_language_file(filepath, base_translations, fallback_translations):
            updated_count += 1
            print("OK")
        else:
            skipped_count += 1
            print("SKIPPED")
    
    print()
    print(f"Done! Updated {updated_count} files, skipped {skipped_count} files.")

def count_keys(d, prefix=''):
    """Count total number of leaf keys in a nested dict."""
    count = 0
    for key, value in d.items():
        if isinstance(value, dict):
            count += count_keys(value, f"{prefix}{key}.")
        else:
            count += 1
    return count

if __name__ == '__main__':
    main()
