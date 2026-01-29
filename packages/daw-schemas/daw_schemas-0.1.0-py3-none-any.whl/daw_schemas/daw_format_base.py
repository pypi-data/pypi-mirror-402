#!/usr/bin/env python3
"""
Base classes for DAW format analysis.

This module provides a reusable framework for analyzing different DAW file
formats. Extend these classes to add support for new formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Set, Optional
from collections import defaultdict
import json
import sys


class DAWFormatAnalyzer(ABC):
    """Base class for analyzing DAW file formats."""

    def __init__(self):
        self.element_info: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'attributes': defaultdict(int),
            'children': defaultdict(int),
            'parents': set(),
            'has_text': False
        })
        self.hierarchy: Dict[str, Set[str]] = defaultdict(set)
        self.versions: Set[str] = set()
        self.format_name: str = "Unknown"

    @abstractmethod
    def load_file(self, file_path: Path) -> Any:
        """Load and parse a DAW file. Returns parsed structure."""
        pass

    @abstractmethod
    def extract_version(self, parsed: Any) -> Optional[str]:
        """Extract version information from parsed file."""
        pass

    @abstractmethod
    def analyze_structure(self, parsed: Any) -> None:
        """Analyze the structure of a parsed file."""
        pass

    def analyze_file(self, file_path: Path, max_elements: int = 50000) -> bool:
        """Analyze a single file."""
        try:
            parsed = self.load_file(file_path)
            version = self.extract_version(parsed)
            if version:
                self.versions.add(version)
            self.analyze_structure(parsed)
            return True
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
            return False

    @abstractmethod
    def generate_schema(self) -> Dict[str, Any]:
        """Generate a JSON schema from the analysis."""
        pass

    def save_schema(self, output_path: Path):
        """Save the generated schema to a file."""
        schema = self.generate_schema()
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)


class DAWFileComparator(ABC):
    """Base class for comparing DAW files."""

    def __init__(self, schema_path: Optional[Path] = None):
        self.schema: Optional[Dict[str, Any]] = None
        if schema_path and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)

    @abstractmethod
    def load_file(self, file_path: Path) -> tuple:
        """Load a file and return (parsed_structure, metadata)."""
        pass

    @abstractmethod
    def compare(self, file1: Path, file2: Path) -> Dict[str, Any]:
        """Compare two files and return differences."""
        pass

    def print_comparison(self, comparison: Dict[str, Any],
                        show_details: bool = True):
        """Print comparison results in a readable format."""
        print("=" * 70)
        print(f"{self.format_name} File Comparison")
        print("=" * 70)

        print(f"\nFile 1: {Path(comparison['file1']).name}")
        if 'metadata' in comparison and 'file1' in comparison['metadata']:
            meta1 = comparison['metadata']['file1']
            if 'version' in meta1:
                print(f"  Version: {meta1['version']}")

        print(f"\nFile 2: {Path(comparison['file2']).name}")
        if 'metadata' in comparison and 'file2' in comparison['metadata']:
            meta2 = comparison['metadata']['file2']
            if 'version' in meta2:
                print(f"  Version: {meta2['version']}")

        if 'summary' in comparison:
            summary = comparison['summary']
            print(f"\n{'=' * 70}")
            print("Summary")
            print(f"{'=' * 70}")
            print(f"Total differences: {summary.get('total_differences', 0)}")

        if show_details and 'differences' in comparison:
            print(f"\n{'=' * 70}")
            print("Differences")
            print(f"{'=' * 70}")
            for i, diff in enumerate(comparison['differences'][:50], 1):
                print(f"\n[{i}] {diff.get('type', 'unknown').upper()}")
                if 'path' in diff:
                    print(f"    Path: {diff['path']}")
                for key in ['attribute', 'file1_value', 'file2_value', 'issue']:
                    if key in diff:
                        print(f"    {key}: {diff[key]}")


# Example implementation for Ableton Live
class ALSFormatAnalyzer(DAWFormatAnalyzer):
    """Ableton Live .als format analyzer."""

    def __init__(self):
        super().__init__()
        self.format_name = "Ableton Live .als"

    def load_file(self, file_path: Path):
        """Load .als file (gzipped XML)."""
        import gzip
        import xml.etree.ElementTree as ET

        with gzip.open(file_path, 'rb') as f:
            xml_content = f.read()
        return ET.fromstring(xml_content)

    def extract_version(self, parsed):
        """Extract Ableton Live version."""
        return parsed.attrib.get('Creator', '')

    def analyze_structure(self, parsed):
        """Analyze XML structure."""
        # Implementation would go here
        # This is a simplified version
        pass

    def generate_schema(self):
        """Generate schema."""
        return {
            'format': self.format_name,
            'versions': sorted(list(self.versions))
        }


if __name__ == '__main__':
    # Example usage
    import sys
    analyzer = ALSFormatAnalyzer()
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if analyzer.analyze_file(file_path):
            schema = analyzer.generate_schema()
            print(json.dumps(schema, indent=2))

