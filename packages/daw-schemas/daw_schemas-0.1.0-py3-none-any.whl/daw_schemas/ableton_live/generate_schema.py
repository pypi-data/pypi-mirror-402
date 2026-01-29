#!/usr/bin/env python3
"""
Generate a structural JSON schema for Ableton Live .als files.

This schema describes the XML structure of .als files - all elements,
attributes, and their relationships. It is not specific to any particular
file, but describes the structure that all .als files follow.
"""

import gzip
import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Set, List, Optional
import argparse


class ALSComparisonSchemaGenerator:
    """Generate a structural schema describing .als XML format."""

    def __init__(self):
        self.element_info: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'attributes': defaultdict(int),
            'children': defaultdict(int),
            'parents': set(),
            'has_text': False,
            'is_identifier': False,
            'is_value': False
        })
        self.hierarchy: Dict[str, Set[str]] = defaultdict(set)
        self.versions: Set[str] = set()

    def analyze_file(self, file_path: Path, max_elements: int = 50000) -> bool:
        """Analyze a single .als file."""
        try:
            with gzip.open(file_path, 'rb') as f:
                xml_content = f.read()

            root = ET.fromstring(xml_content)

            # Extract version
            creator = root.attrib.get('Creator', '')
            if creator:
                self.versions.add(creator)

            element_count = [0]
            self._analyze_element(root, None, 0, element_count, max_elements)
            return True
        except Exception as e:
            print(f"Error: {file_path}: {e}", file=sys.stderr)
            return False

    def _analyze_element(self, element: ET.Element, parent_tag: Optional[str],
                         depth: int, element_count: List[int], max_elements: int):
        """Recursively analyze elements."""
        if element_count[0] >= max_elements:
            return

        tag = element.tag
        info = self.element_info[tag]
        info['count'] += 1

        if parent_tag:
            info['parents'].add(parent_tag)
            self.hierarchy[parent_tag].add(tag)

        # Analyze attributes
        for attr_name, attr_value in element.attrib.items():
            info['attributes'][attr_name] += 1

            # Identify common identifier patterns
            if attr_name.lower() in ['id', 'lomid', 'refid', 'key']:
                info['is_identifier'] = True

        # Check for text content
        if element.text and element.text.strip():
            info['has_text'] = True
            # Identify value elements
            text = element.text.strip()
            if tag.endswith('Value') or tag.endswith('Id') or tag.endswith('Index'):
                info['is_value'] = True

        element_count[0] += 1
        if depth < 15:  # Limit recursion depth
            for child in element:
                self._analyze_element(child, tag, depth + 1,
                                    element_count, max_elements)

    def generate_comparison_schema(self) -> Dict[str, Any]:
        """Generate a structural schema describing .als XML format."""
        # Identify key structural elements
        key_elements = self._identify_key_elements()

        schema = {
            'schema_version': '1.0',
            'daw_format': 'Ableton Live .als',
            'metadata': {
                'versions_analyzed': sorted(list(self.versions)),
                'total_element_types': len(self.element_info),
                'description': 'Structural schema describing XML elements, attributes, and hierarchy for all .als files'
            },
            'root_structure': {
                'Ableton': {
                    'required_attributes': ['Creator', 'MajorVersion',
                                          'MinorVersion', 'Revision'],
                    'children': ['LiveSet']
                }
            },
            'key_sections': self._build_key_sections(),
            'track_structure': self._build_track_structure(),
            'element_catalog': self._build_element_catalog(key_elements)
        }

        return schema

    def _identify_key_elements(self) -> Set[str]:
        """Identify elements that are important for comparison."""
        key_elements = set()

        # High-level structure
        key_elements.add('LiveSet')
        key_elements.add('Tracks')
        key_elements.add('Scenes')
        key_elements.add('Transport')

        # Track types
        key_elements.update(['AudioTrack', 'MidiTrack', 'GroupTrack',
                           'ReturnTrack', 'MainTrack', 'PreHearTrack'])

        # Common structural elements
        for tag, info in self.element_info.items():
            if info['count'] > 100:  # Frequently occurring
                key_elements.add(tag)
            if info['is_identifier']:
                key_elements.add(tag)

        return key_elements

    def _build_key_sections(self) -> Dict[str, Any]:
        """Build schema for key LiveSet sections."""
        sections = {}

        # Get LiveSet children
        if 'LiveSet' in self.hierarchy:
            for section_tag in sorted(self.hierarchy['LiveSet']):
                if section_tag in self.element_info:
                    info = self.element_info[section_tag]
                    # Determine required attributes (present in all occurrences)
                    required_attrs = [
                        attr for attr, count in info['attributes'].items()
                        if count == info['count'] and info['count'] > 0
                    ]
                    sections[section_tag] = {
                        'attributes': sorted(list(info['attributes'].keys())),
                        'required_attributes': required_attrs,
                        'children': sorted(list(
                            self.hierarchy.get(section_tag, set()))),
                        'has_identifiers': info['is_identifier']
                    }

        return sections

    def _build_track_structure(self) -> Dict[str, Any]:
        """Build schema for track types."""
        track_types = ['AudioTrack', 'MidiTrack', 'GroupTrack',
                      'ReturnTrack', 'MainTrack', 'PreHearTrack']

        structure = {}
        for track_type in track_types:
            if track_type in self.element_info:
                info = self.element_info[track_type]
                # Determine required attributes (present in all occurrences)
                required_attrs = [
                    attr for attr, count in info['attributes'].items()
                    if count == info['count'] and info['count'] > 0
                ]
                structure[track_type] = {
                    'attributes': sorted(list(info['attributes'].keys())),
                    'required_attributes': required_attrs,
                    'children': sorted(list(
                        self.hierarchy.get(track_type, set()))),
                    'identifier_attributes': [
                        attr for attr in info['attributes'].keys()
                        if attr.lower() in ['id', 'lomid', 'refid']
                    ]
                }

        return structure

    def _build_element_catalog(self, key_elements: Set[str]) -> Dict[str, Any]:
        """Build catalog of all XML elements with their structure."""
        catalog = {}

        # Include all elements found, sorted alphabetically
        for tag in sorted(self.element_info.keys()):
            info = self.element_info[tag]
            # Determine required attributes (present in all occurrences)
            required_attrs = [
                attr for attr, count in info['attributes'].items()
                if count == info['count'] and info['count'] > 0
            ]
            catalog[tag] = {
                'attributes': sorted(list(info['attributes'].keys())),
                'required_attributes': required_attrs,
                'parents': sorted(list(info['parents'])),
                'children': sorted(list(
                    self.hierarchy.get(tag, set()))),
                'has_text': info['has_text'],
                'is_identifier': info['is_identifier'],
                'is_value': info['is_value'],
                'is_key_element': tag in key_elements
            }

        return catalog


def main():
    parser = argparse.ArgumentParser(
        description='Generate structural schema for .als files (describes XML structure)')
    parser.add_argument('directories', nargs='+', help='Directory(ies) containing .als files')
    parser.add_argument('--sample-size', type=int, default=20,
                       help='Number of files to analyze')
    parser.add_argument('--output', '-o', default='12/schema.json',
                       help='Output JSON file path (relative to script directory)')
    parser.add_argument('--max-elements', type=int, default=40000,
                       help='Max elements per file')

    args = parser.parse_args()

    # Find .als files from all provided directories
    als_files = []
    for directory in args.directories:
        directory = Path(directory)
        if not directory.exists():
            print(f"Warning: Directory does not exist: {directory}", file=sys.stderr)
            continue
        als_files.extend(directory.rglob('*.als'))
    
    if not als_files:
        print(f"Error: No .als files found in provided directories", file=sys.stderr)
        sys.exit(1)
    main_files = [f for f in als_files if 'Backup' not in str(f)]
    backup_files = [f for f in als_files if 'Backup' in str(f)]

    sample_files = main_files[:args.sample_size]
    if len(sample_files) < args.sample_size and backup_files:
        sample_files.extend(backup_files[:args.sample_size - len(sample_files)])

    print(f"Analyzing {len(sample_files)} files for comparison schema...")

    generator = ALSComparisonSchemaGenerator()

    for i, als_file in enumerate(sample_files, 1):
        print(f"[{i}/{len(sample_files)}] {als_file.name}...", end=' ')
        success = generator.analyze_file(als_file, args.max_elements)
        print("✓" if success else "✗")

    schema = generator.generate_comparison_schema()

    # Save schema (resolve path relative to script directory)
    script_dir = Path(__file__).parent
    output_path = script_dir / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)

    print(f"\n✓ Structural schema written to {output_path}")
    print(f"  Element types: {len(generator.element_info)}")
    print(f"  Key sections: {len(schema['key_sections'])}")
    print(f"  Track types: {len(schema['track_structure'])}")


if __name__ == '__main__':
    main()

