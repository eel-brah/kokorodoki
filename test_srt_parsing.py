#!/usr/bin/env python3
"""Simple test for SRT parsing functionality without dependencies"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class SRTEntry:
    """Represents a single SRT subtitle entry"""
    index: int
    start_time: float  # in seconds
    end_time: float    # in seconds
    text: str


def parse_srt_timestamp(timestamp: str) -> float:
    """Parse SRT timestamp format (HH:MM:SS,mmm) to seconds"""
    # Replace comma with dot for milliseconds
    timestamp = timestamp.replace(',', '.')
    parts = timestamp.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_ms = float(parts[2])
    
    return hours * 3600 + minutes * 60 + seconds_ms


def parse_srt_file(file_path: str) -> List[SRTEntry]:
    """Parse an SRT subtitle file and return a list of SRTEntry objects"""
    entries = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Split by double newlines to separate entries
    blocks = re.split(r'\n\s*\n', content)
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
            
        try:
            # Parse index
            index = int(lines[0])
            
            # Parse timestamp line
            timestamp_line = lines[1]
            timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timestamp_line)
            if not timestamp_match:
                continue
                
            start_time = parse_srt_timestamp(timestamp_match.group(1))
            end_time = parse_srt_timestamp(timestamp_match.group(2))
            
            # Join text lines (in case subtitle spans multiple lines)
            text = '\n'.join(lines[2:]).strip()
            
            entries.append(SRTEntry(index, start_time, end_time, text))
            
        except (ValueError, IndexError):
            # Skip malformed entries
            continue
    
    return entries


if __name__ == "__main__":
    # Test the SRT parsing function
    try:
        entries = parse_srt_file('test_subtitle.srt')
        print(f'Successfully parsed {len(entries)} SRT entries:')
        print()
        
        for entry in entries:
            print(f'Entry {entry.index}:')
            print(f'  Time: {entry.start_time:.1f}s - {entry.end_time:.1f}s (duration: {entry.end_time - entry.start_time:.1f}s)')
            print(f'  Text: "{entry.text}"')
            print()
            
        print("✅ SRT parsing test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing SRT parsing: {e}")
