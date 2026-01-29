#!/usr/bin/env python3
"""
Smart comparison of .als files using schema to filter meaningful changes.

This enhanced version uses the schema to:
- Ignore irrelevant differences (like internal IDs)
- Focus on structural and content changes
- Group related changes together
- Provide more meaningful diff output
"""

import gzip
import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict
import argparse


class SmartALSComparator:
    """Compare .als files with schema-aware filtering."""

    def __init__(self, schema_path: Optional[Path] = None):
        self.schema: Optional[Dict[str, Any]] = None
        self.ignore_attributes: Set[str] = set()
        self.key_elements: Set[str] = set()

        if schema_path and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)
            self._load_schema_info()

    def _load_schema_info(self):
        """Extract useful information from schema."""
        if not self.schema:
            return

        # Identify attributes that are likely internal IDs (not meaningful changes)
        element_catalog = self.schema.get('element_catalog', {})
        for element_name, info in element_catalog.items():
            # Mark identifier attributes (these change frequently but aren't meaningful)
            if info.get('is_identifier'):
                for attr in info.get('attributes', []):
                    if attr.lower() in ['id', 'lomid', 'refid', 'key']:
                        self.ignore_attributes.add(attr)

        # Identify key structural elements
        key_sections = self.schema.get('key_sections', {})
        self.key_elements.update(key_sections.keys())

        track_structure = self.schema.get('track_structure', {})
        self.key_elements.update(track_structure.keys())

    def load_als(self, file_path: Path) -> tuple:
        """Load and parse an .als file."""
        with gzip.open(file_path, 'rb') as f:
            xml_content = f.read()

        root = ET.fromstring(xml_content)

        metadata = {
            'version': root.attrib.get('Creator', 'Unknown'),
            'major_version': root.attrib.get('MajorVersion', ''),
            'minor_version': root.attrib.get('MinorVersion', ''),
            'revision': root.attrib.get('Revision', '')
        }

        return root, metadata

    def compare(self, file1: Path, file2: Path) -> Dict[str, Any]:
        """Compare two .als files with smart filtering and semantic interpretation."""
        root1, meta1 = self.load_als(file1)
        root2, meta2 = self.load_als(file2)

        comparison = {
            'file1': str(file1),
            'file2': str(file2),
            'metadata': {
                'file1': meta1,
                'file2': meta2
            },
            'differences': {
                'structural': [],
                'content': [],
                'settings': [],
                'ignored': []
            },
            'semantic_changes': {
                'tracks_added': [],
                'tracks_removed': [],
                'plugins_added': [],
                'plugins_removed': [],
                'parameters_changed': [],
                'tempo_changed': None
            },
            'summary': {}
        }

        # Compare root
        root_diff = self._compare_attributes(root1, root2, 'root',
                                            ignore_internal=True)
        if root_diff:
            comparison['differences']['settings'].extend(root_diff)

        # Compare LiveSet
        liveset1 = root1.find('LiveSet')
        liveset2 = root2.find('LiveSet')

        if liveset1 is not None and liveset2 is not None:
            liveset_diff = self._compare_elements_smart(
                liveset1, liveset2, 'LiveSet')
            comparison['differences'].update(liveset_diff)

            # Extract semantic changes
            self._extract_semantic_changes(liveset1, liveset2, comparison)

        # Generate summary
        comparison['summary'] = {
            'version_changed': meta1['version'] != meta2['version'],
            'revision_changed': meta1['revision'] != meta2['revision'],
            'structural_changes': len(comparison['differences']['structural']),
            'content_changes': len(comparison['differences']['content']),
            'settings_changes': len(comparison['differences']['settings']),
            'ignored_changes': len(comparison['differences']['ignored']),
            'total_meaningful_changes': (
                len(comparison['differences']['structural']) +
                len(comparison['differences']['content']) +
                len(comparison['differences']['settings'])
            ),
            'semantic_changes': {
                'tracks_added': len(comparison['semantic_changes']['tracks_added']),
                'tracks_removed': len(comparison['semantic_changes']['tracks_removed']),
                'plugins_added': len(comparison['semantic_changes']['plugins_added']),
                'plugins_removed': len(comparison['semantic_changes']['plugins_removed']),
                'parameters_changed': len(comparison['semantic_changes']['parameters_changed']),
                'tempo_changed': comparison['semantic_changes']['tempo_changed'] is not None
            }
        }

        return comparison

    def _extract_semantic_changes(self, liveset1: ET.Element, liveset2: ET.Element,
                                  comparison: Dict[str, Any]):
        """Extract semantic changes using the same logic as SemanticALSComparator."""
        # Import semantic extraction methods (we'll add them to this class)
        tracks1_elem = liveset1.find('Tracks')
        tracks2_elem = liveset2.find('Tracks')

        if tracks1_elem is None or tracks2_elem is None:
            return

        # Get tracks with IDs
        tracks1_by_id = {}
        tracks2_by_id = {}

        for track in tracks1_elem:
            track_id = track.attrib.get('Id', '')
            track_name = self._get_track_name(track)
            if track_id:
                tracks1_by_id[track_id] = (track_name, track)

        for track in tracks2_elem:
            track_id = track.attrib.get('Id', '')
            track_name = self._get_track_name(track)
            if track_id:
                tracks2_by_id[track_id] = (track_name, track)

        # Find added/removed tracks
        for track_id, (name, _) in tracks2_by_id.items():
            if track_id not in tracks1_by_id:
                comparison['semantic_changes']['tracks_added'].append(name)

        for track_id, (name, _) in tracks1_by_id.items():
            if track_id not in tracks2_by_id:
                comparison['semantic_changes']['tracks_removed'].append(name)

        # Compare tracks for plugins and parameters
        common_track_ids = set(tracks1_by_id.keys()) & set(tracks2_by_id.keys())
        for track_id in common_track_ids:
            name1, track1 = tracks1_by_id[track_id]
            name2, track2 = tracks2_by_id[track_id]
            track_name = name1

            # Get devices from tracks
            devices1 = self._get_track_devices(track1)
            devices2 = self._get_track_devices(track2)

            devices1_by_id = {dev_id: (name, dev) for dev_id, name, dev in devices1}
            devices2_by_id = {dev_id: (name, dev) for dev_id, name, dev in devices2}

            # Find added/removed plugins
            for dev_id, (plugin_name, _) in devices2_by_id.items():
                if dev_id not in devices1_by_id:
                    comparison['semantic_changes']['plugins_added'].append({
                        'plugin': plugin_name,
                        'track': track_name
                    })

            for dev_id, (plugin_name, _) in devices1_by_id.items():
                if dev_id not in devices2_by_id:
                    comparison['semantic_changes']['plugins_removed'].append({
                        'plugin': plugin_name,
                        'track': track_name
                    })

            # Compare parameters in common devices
            common_device_ids = set(devices1_by_id.keys()) & set(devices2_by_id.keys())
            for dev_id in common_device_ids:
                plugin_name1, device1 = devices1_by_id[dev_id]
                plugin_name2, device2 = devices2_by_id[dev_id]
                plugin_name = plugin_name1

                # Extract and compare parameters
                # For VST/AU plugins, we need to match by position for parameters with "-1" IDs
                if device1.tag in ['PluginDevice', 'AuPluginDevice', 'Vst3PluginDevice']:
                    self._compare_vst_parameters(device1, device2, plugin_name, track_name, comparison)
                else:
                    # Stock plugins: simple parameter comparison
                    params1 = self._get_device_parameters(device1)
                    params2 = self._get_device_parameters(device2)

                    # Find changed parameters
                    all_params = set(params1.keys()) | set(params2.keys())
                    for param_name in all_params:
                        val1 = params1.get(param_name, '')
                        val2 = params2.get(param_name, '')
                        if val1 != val2:
                            # Determine change type
                            try:
                                num_val1 = float(val1) if val1 else 0.0
                                num_val2 = float(val2) if val2 else 0.0
                                if num_val2 > num_val1:
                                    change_type = 'increased'
                                elif num_val2 < num_val1:
                                    change_type = 'decreased'
                                else:
                                    change_type = 'changed'
                            except (ValueError, TypeError):
                                change_type = 'changed'

                            comparison['semantic_changes']['parameters_changed'].append({
                                'parameter': param_name.replace('_', ' '),
                                'plugin': plugin_name,
                                'track': track_name,
                                'change': change_type,
                                'from': val1,
                                'to': val2
                            })

    def _compare_vst_parameters(self, device1: ET.Element, device2: ET.Element,
                               plugin_name: str, track_name: str, comparison: Dict[str, Any]):
        """Compare VST/AU plugin parameters, handling "-1" IDs by position matching."""
        param_list1 = device1.find('ParameterList')
        param_list2 = device2.find('ParameterList')

        if param_list1 is None or param_list2 is None:
            return

        params1_list = param_list1.findall('PluginFloatParameter') + param_list1.findall('PluginEnumParameter')
        params2_list = param_list2.findall('PluginFloatParameter') + param_list2.findall('PluginEnumParameter')

        # Collect parameter data
        params1_data = []
        params2_data = []

        for p in params1_list:
            param_id_elem = p.find('ParameterId')
            param_name_elem = p.find('ParameterName')
            param_value_elem = p.find('ParameterValue')

            if param_value_elem is not None:
                manual = param_value_elem.find('Manual')
                value = manual.attrib.get('Value', '') if manual is not None else ''

                param_id = param_id_elem.attrib.get('Value', '') if param_id_elem is not None else ''
                name = ''
                if param_name_elem is not None:
                    name_val = param_name_elem.attrib.get('Value', '').strip()
                    if name_val:
                        name = name_val

                params1_data.append((param_id, name, value))

        for p in params2_list:
            param_id_elem = p.find('ParameterId')
            param_name_elem = p.find('ParameterName')
            param_value_elem = p.find('ParameterValue')

            if param_value_elem is not None:
                manual = param_value_elem.find('Manual')
                value = manual.attrib.get('Value', '') if manual is not None else ''

                param_id = param_id_elem.attrib.get('Value', '') if param_id_elem is not None else ''
                name = ''
                if param_name_elem is not None:
                    name_val = param_name_elem.attrib.get('Value', '').strip()
                    if name_val:
                        name = name_val

                params2_data.append((param_id, name, value))

        # Match parameters: first by ID, then by position
        params1_by_id = {}
        params2_by_id = {}
        params1_by_pos = {}
        params2_by_pos = {}

        for idx, (param_id, name, value) in enumerate(params1_data):
            if param_id and param_id != '-1':
                params1_by_id[param_id] = (name, value)
            params1_by_pos[idx] = (name, value)

        for idx, (param_id, name, value) in enumerate(params2_data):
            if param_id and param_id != '-1':
                params2_by_id[param_id] = (name, value)
            params2_by_pos[idx] = (name, value)

        # Compare parameters matched by ID first
        common_param_ids = set(params1_by_id.keys()) & set(params2_by_id.keys())
        for param_id in common_param_ids:
            name1, val1 = params1_by_id[param_id]
            name2, val2 = params2_by_id[param_id]

            if val1 != val2:
                # Use ParameterName if available, otherwise use ParameterId
                if name1 and name1 != param_id and name1 != '-1':
                    param_name = name1.replace('_', ' ')
                elif param_id and param_id != '-1':
                    param_name = f"Parameter {param_id}"
                else:
                    param_name = f"Parameter {param_id}"

                # Determine change type
                try:
                    num_val1 = float(val1) if val1 else 0.0
                    num_val2 = float(val2) if val2 else 0.0
                    if num_val2 > num_val1:
                        change_type = 'increased'
                    elif num_val2 < num_val1:
                        change_type = 'decreased'
                    else:
                        change_type = 'changed'
                except (ValueError, TypeError):
                    change_type = 'changed'

                comparison['semantic_changes']['parameters_changed'].append({
                    'parameter': param_name,
                    'plugin': plugin_name,
                    'track': track_name,
                    'change': change_type,
                    'from': val1,
                    'to': val2
                })

        # Compare parameters by position for those without valid IDs
        max_pos = min(len(params1_by_pos), len(params2_by_pos))
        for idx in range(max_pos):
            name1, val1 = params1_by_pos[idx]
            name2, val2 = params2_by_pos[idx]

            # Only compare if not already matched by ID
            param_id1 = params1_data[idx][0] if idx < len(params1_data) else ''
            if not (param_id1 and param_id1 != '-1' and param_id1 in common_param_ids):
                if val1 != val2:
                    # Use ParameterName if available, otherwise use index
                    if name1 and name1 != '-1' and name1 != param_id1:
                        param_name = name1.replace('_', ' ')
                    elif param_id1 and param_id1 != '-1':
                        param_name = f"Parameter {param_id1}"
                    else:
                        param_name = f"Parameter {idx + 1}"  # +1 for 1-based indexing

                    # Determine change type
                    try:
                        num_val1 = float(val1) if val1 else 0.0
                        num_val2 = float(val2) if val2 else 0.0
                        if num_val2 > num_val1:
                            change_type = 'increased'
                        elif num_val2 < num_val1:
                            change_type = 'decreased'
                        else:
                            change_type = 'changed'
                    except (ValueError, TypeError):
                        change_type = 'changed'

                    comparison['semantic_changes']['parameters_changed'].append({
                        'parameter': param_name,
                        'plugin': plugin_name,
                        'track': track_name,
                        'change': change_type,
                        'from': val1,
                        'to': val2
                    })

    def _get_track_name(self, track: ET.Element) -> str:
        """Extract track name."""
        name_elem = track.find('Name')
        if name_elem is not None:
            effective_name = name_elem.find('EffectiveName')
            if effective_name is not None:
                val = effective_name.attrib.get('Value', '').strip()
                if val:
                    return val
            user_name = name_elem.find('UserName')
            if user_name is not None:
                val = user_name.attrib.get('Value', '').strip()
                if val:
                    return val
        return track.tag

    def _get_track_devices(self, track: ET.Element) -> List[Tuple[str, str, ET.Element]]:
        """Extract devices from a track. Returns (id, name, device)."""
        result = []
        device_chain = track.find('DeviceChain')
        if device_chain is None:
            return result
        nested_chain = device_chain.find('DeviceChain')
        if nested_chain is None:
            return result
        devices_elem = nested_chain.find('Devices')
        if devices_elem is None:
            return result

        for device in devices_elem:
            device_id = device.attrib.get('Id', '')
            name = self._get_plugin_name(device)
            result.append((device_id, name, device))

            # Handle nested devices in group devices
            if device.tag in ['DrumGroupDevice', 'AudioEffectGroupDevice', 'InstrumentGroupDevice']:
                def find_nested_devices(group_dev, prefix_id, prefix_name, depth=0):
                    nested = []
                    if depth > 5:
                        return nested
                    return_branches = group_dev.find('ReturnBranches')
                    if return_branches is not None:
                        for return_branch in return_branches.findall('ReturnBranch'):
                            for devices_elem in return_branch.findall('.//Devices'):
                                for nested_device in devices_elem:
                                    nested_device_id = nested_device.attrib.get('Id', '')
                                    nested_device_name = self._get_plugin_name(nested_device)
                                    composite_id = f"{prefix_id}_return_{nested_device_id}"
                                    nested.append((composite_id, nested_device_name, nested_device))
                                    if nested_device.tag in ['DrumGroupDevice', 'AudioEffectGroupDevice', 'InstrumentGroupDevice']:
                                        nested.extend(find_nested_devices(nested_device, composite_id, nested_device_name, depth + 1))
                    branches = group_dev.find('Branches')
                    if branches is not None:
                        for branch in branches:
                            for devices_elem in branch.findall('.//Devices'):
                                for nested_device in devices_elem:
                                    nested_device_id = nested_device.attrib.get('Id', '')
                                    nested_device_name = self._get_plugin_name(nested_device)
                                    composite_id = f"{prefix_id}_branch_{nested_device_id}"
                                    nested.append((composite_id, nested_device_name, nested_device))
                                    if nested_device.tag in ['DrumGroupDevice', 'AudioEffectGroupDevice', 'InstrumentGroupDevice']:
                                        nested.extend(find_nested_devices(nested_device, composite_id, nested_device_name, depth + 1))
                    return nested

                nested_devices = find_nested_devices(device, device_id, name)
                result.extend(nested_devices)

        return result

    def _get_plugin_name(self, device: ET.Element) -> str:
        """Extract plugin name."""
        user_name = device.find('UserName')
        if user_name is not None:
            val = user_name.attrib.get('Value', '').strip()
            if val:
                return val

        # Check PluginDesc for VST info
        plugin_desc = device.find('PluginDesc')
        if plugin_desc is not None:
            vst3_info = plugin_desc.find('Vst3PluginInfo')
            if vst3_info is not None:
                name_elem = vst3_info.find('Name')
                if name_elem is not None:
                    val = name_elem.attrib.get('Value', '').strip()
                    if val:
                        return val
            au_info = plugin_desc.find('AuPluginInfo')
            if au_info is not None:
                name_elem = au_info.find('Name')
                if name_elem is not None:
                    val = name_elem.attrib.get('Value', '').strip()
                    if val:
                        return val

        return device.tag

    def _get_device_parameters(self, device: ET.Element) -> Dict[str, str]:
        """Extract parameters from a device (generic approach)."""
        params = {}
        device_tag = device.tag

        # VST/AU plugins use ParameterList
        if device_tag in ['PluginDevice', 'AuPluginDevice', 'Vst3PluginDevice']:
            param_list = device.find('ParameterList')
            if param_list is not None:
                for param in param_list.findall('PluginFloatParameter') + param_list.findall('PluginEnumParameter'):
                    param_id_elem = param.find('ParameterId')
                    param_name_elem = param.find('ParameterName')
                    param_value_elem = param.find('ParameterValue')

                    if param_value_elem is not None:
                        manual = param_value_elem.find('Manual')
                        value = manual.attrib.get('Value', '') if manual is not None else ''

                        param_id = param_id_elem.attrib.get('Value', '') if param_id_elem is not None else ''
                        name = ''
                        if param_name_elem is not None:
                            name_val = param_name_elem.attrib.get('Value', '').strip()
                            if name_val:
                                name = name_val

                        # Skip parameters with invalid IDs or empty names
                        if param_id and param_id != '-1' and name and name != '-1':
                            params[param_id] = (name, value)
                        elif name and name != '-1' and name != param_id:
                            # If we have a valid name but invalid ID, use name as key
                            params[name] = (name, value)

            # Convert to dict with names as keys, filtering out empty or invalid names
            return {name: value for name, value in params.values()
                   if name and name != '-1' and name.strip()}

        # Stock plugins: extract generically
        if device_tag not in ['DrumGroupDevice', 'AudioEffectGroupDevice', 'InstrumentGroupDevice']:
            params = self._extract_stock_plugin_parameters(device)
            return params

        return params

    def _extract_stock_plugin_parameters(self, element: ET.Element, path: str = '') -> Dict[str, str]:
        """Recursively extract parameters from stock plugins."""
        params = {}

        manual = element.find('Manual')
        if manual is not None:
            value = manual.attrib.get('Value', '')
            if value:
                param_name = path if path else element.tag
                if element.tag not in ['LomId', 'LomIdView', 'IsExpanded', 'BreakoutIsExpanded',
                                      'ModulationSourceCount', 'Pointee', 'LastSelectedTimeableIndex',
                                      'LastSelectedClipEnvelopeIndex', 'LastPresetRef', 'LockedScripts',
                                      'IsFolded', 'ShouldShowPresetName', 'UserName', 'Annotation',
                                      'SourceContext', 'MpePitchBendUsesTuning', 'ViewData', 'OverwriteProtectionNumber',
                                      'On', 'ParametersListWrapper', 'ParameterList', 'DeviceChain', 'Devices',
                                      'Branches', 'ReturnBranches', 'SpectrumAnalyzer', 'LastUserRange',
                                      'LastInternalRange', 'AutomationTarget', 'ModulationTarget', 'MidiControllerRange',
                                      'MidiCCOnOffThresholds', 'PluginDesc', 'PluginFloatParameter', 'PluginEnumParameter',
                                      'ParameterId', 'ParameterName', 'ParameterValue']:
                    params[param_name] = value

        for child in element:
            if child.tag in ['LomId', 'LomIdView', 'IsExpanded', 'BreakoutIsExpanded',
                            'ModulationSourceCount', 'Pointee', 'LastSelectedTimeableIndex',
                            'LastSelectedClipEnvelopeIndex', 'LastPresetRef', 'LockedScripts',
                            'IsFolded', 'ShouldShowPresetName', 'UserName', 'Annotation',
                            'SourceContext', 'MpePitchBendUsesTuning', 'ViewData', 'OverwriteProtectionNumber',
                            'On', 'ParametersListWrapper', 'ParameterList', 'DeviceChain', 'Devices',
                            'Branches', 'ReturnBranches', 'SpectrumAnalyzer', 'LastUserRange',
                            'LastInternalRange', 'AutomationTarget', 'ModulationTarget', 'MidiControllerRange',
                            'MidiCCOnOffThresholds', 'PluginDesc', 'PluginFloatParameter', 'PluginEnumParameter',
                            'ParameterId', 'ParameterName', 'ParameterValue']:
                continue

            child_path = f'{path}.{child.tag}' if path else child.tag

            if '.' in child.tag and child.tag[0].isupper():
                parts = child.tag.split('.')
                if len(parts) == 2 and parts[1].isdigit():
                    base_name = parts[0].rstrip('s')
                    index = int(parts[1]) + 1
                    child_path = f'{base_name} {index}' if not path else f'{path} {base_name} {index}'

            if 'ParameterA' in child_path:
                child_path = child_path.replace('ParameterA', 'A')
            elif 'ParameterB' in child_path:
                child_path = child_path.replace('ParameterB', 'B')

            child_path = child_path.replace('.', ' ')

            child_params = self._extract_stock_plugin_parameters(child, child_path)
            params.update(child_params)

        return params

    def _compare_elements_smart(self, elem1: ET.Element, elem2: ET.Element,
                                path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Compare elements with smart filtering."""
        differences = {
            'structural': [],
            'content': [],
            'settings': [],
            'ignored': []
        }

        # Compare attributes (filter internal IDs)
        attr_diff = self._compare_attributes(elem1, elem2, path,
                                            ignore_internal=True)

        # Categorize attribute differences
        for diff in attr_diff:
            attr_name = diff.get('attribute', '')
            if attr_name in self.ignore_attributes:
                differences['ignored'].append(diff)
            elif self._is_setting_attribute(path, attr_name):
                differences['settings'].append(diff)
            else:
                differences['content'].append(diff)

        # Compare text content
        text1 = elem1.text.strip() if elem1.text else None
        text2 = elem2.text.strip() if elem2.text else None
        if text1 != text2:
            diff = {
                'type': 'content',
                'path': path,
                'file1_value': text1,
                'file2_value': text2
            }
            if self._is_meaningful_content(path, text1, text2):
                differences['content'].append(diff)
            else:
                differences['ignored'].append(diff)

        # Compare children structure
        children1 = self._group_children(elem1)
        children2 = self._group_children(elem2)

        all_tags = set(children1.keys()) | set(children2.keys())

        for tag in all_tags:
            child_path = f"{path}/{tag}"
            children_list1 = children1.get(tag, [])
            children_list2 = children2.get(tag, [])

            if len(children_list1) != len(children_list2):
                diff = {
                    'type': 'structural',
                    'path': child_path,
                    'file1_count': len(children_list1),
                    'file2_count': len(children_list2),
                    'element_type': tag
                }

                # Only report if it's a key element or significant change
                if tag in self.key_elements or abs(len(children_list1) - len(children_list2)) > 1:
                    differences['structural'].append(diff)
                else:
                    differences['ignored'].append(diff)

            # Compare matching children (limit depth for performance)
            if path.count('/') < 8:  # Limit recursion depth
                min_count = min(len(children_list1), len(children_list2))
                for i in range(min_count):
                    child_diffs = self._compare_elements_smart(
                        children_list1[i],
                        children_list2[i],
                        f"{child_path}[{i}]"
                    )
                    # Merge child differences
                    for key in differences:
                        differences[key].extend(child_diffs[key])

        return differences

    def _compare_attributes(self, elem1: ET.Element, elem2: ET.Element,
                           path: str, ignore_internal: bool = False) -> List[Dict[str, Any]]:
        """Compare attributes with optional filtering."""
        differences = []

        attrs1 = set(elem1.attrib.keys())
        attrs2 = set(elem2.attrib.keys())

        # Missing attributes
        for attr in attrs1 - attrs2:
            if not (ignore_internal and attr in self.ignore_attributes):
                differences.append({
                    'type': 'attribute',
                    'path': path,
                    'attribute': attr,
                    'issue': f'Missing in file2, value in file1: {elem1.attrib[attr]}'
                })

        for attr in attrs2 - attrs1:
            if not (ignore_internal and attr in self.ignore_attributes):
                differences.append({
                    'type': 'attribute',
                    'path': path,
                    'attribute': attr,
                    'issue': f'Missing in file1, value in file2: {elem2.attrib[attr]}'
                })

        # Different values
        common_attrs = attrs1 & attrs2
        for attr in common_attrs:
            if ignore_internal and attr in self.ignore_attributes:
                continue
            if elem1.attrib[attr] != elem2.attrib[attr]:
                differences.append({
                    'type': 'attribute',
                    'path': path,
                    'attribute': attr,
                    'file1_value': elem1.attrib[attr],
                    'file2_value': elem2.attrib[attr]
                })

        return differences

    def _group_children(self, element: ET.Element) -> Dict[str, List[ET.Element]]:
        """Group children by tag name."""
        grouped = defaultdict(list)
        for child in element:
            grouped[child.tag].append(child)
        return grouped

    def _is_setting_attribute(self, path: str, attr_name: str) -> bool:
        """Check if attribute represents a setting (not content)."""
        setting_paths = ['Transport', 'Grid', 'GlobalQuantisation',
                        'AutomationMode', 'ViewState']
        return any(sp in path for sp in setting_paths) or attr_name == 'Value'

    def _is_meaningful_content(self, path: str, val1: str, val2: str) -> bool:
        """Check if content change is meaningful."""
        # Handle None values
        if val1 is None and val2 is None:
            return False
        if val1 is None or val2 is None:
            return True  # One is None and the other isn't - that's meaningful

        # Ignore very long binary-like content
        if len(val1) > 1000 or len(val2) > 1000:
            return False
        # Ignore if both are empty or whitespace
        if (not val1 or not val1.strip()) and (not val2 or not val2.strip()):
            return False
        return True

    def print_comparison(self, comparison: Dict[str, Any], semantic_only: bool = False):
        """Print comparison results."""
        if semantic_only:
            self._print_semantic_comparison(comparison)
            return

        print("=" * 70)
        print("Smart .als File Comparison")
        print("=" * 70)

        print(f"\nFile 1: {Path(comparison['file1']).name}")
        print(f"  Version: {comparison['metadata']['file1']['version']}")

        print(f"\nFile 2: {Path(comparison['file2']).name}")
        print(f"  Version: {comparison['metadata']['file2']['version']}")

        summary = comparison['summary']
        print(f"\n{'=' * 70}")
        print("Summary")
        print(f"{'=' * 70}")
        print(f"Version changed: {summary['version_changed']}")
        print(f"Revision changed: {summary['revision_changed']}")
        print(f"\nMeaningful changes:")
        print(f"  Structural: {summary['structural_changes']}")
        print(f"  Content: {summary['content_changes']}")
        print(f"  Settings: {summary['settings_changes']}")
        print(f"  Total: {summary['total_meaningful_changes']}")
        print(f"\nIgnored (internal IDs, etc.): {summary['ignored_changes']}")

        # Show semantic changes
        semantic_summary = summary.get('semantic_changes', {})
        if semantic_summary:
            print(f"\n{'=' * 70}")
            print("Semantic Changes")
            print(f"{'=' * 70}")
            print(f"  Tracks added: {semantic_summary.get('tracks_added', 0)}")
            print(f"  Tracks removed: {semantic_summary.get('tracks_removed', 0)}")
            print(f"  Plugins added: {semantic_summary.get('plugins_added', 0)}")
            print(f"  Plugins removed: {semantic_summary.get('plugins_removed', 0)}")
            print(f"  Parameters changed: {semantic_summary.get('parameters_changed', 0)}")
            print(f"  Tempo changed: {semantic_summary.get('tempo_changed', False)}")

            semantic = comparison.get('semantic_changes', {})
            if semantic.get('tracks_added'):
                print(f"\n➕ Added tracks:")
                for track_name in semantic['tracks_added']:
                    print(f"   • {track_name}")

            if semantic.get('tracks_removed'):
                print(f"\n➖ Removed tracks:")
                for track_name in semantic['tracks_removed']:
                    print(f"   • {track_name}")

            if semantic.get('plugins_added'):
                print(f"\n🔌 Added plugins:")
                for plugin_info in semantic['plugins_added']:
                    print(f"   • {plugin_info['plugin']} on track '{plugin_info['track']}'")

            if semantic.get('plugins_removed'):
                print(f"\n🔌 Removed plugins:")
                for plugin_info in semantic['plugins_removed']:
                    print(f"   • {plugin_info['plugin']} from track '{plugin_info['track']}'")

            if semantic.get('parameters_changed'):
                print(f"\n🎛️  Changed parameters:")
                by_track_plugin = defaultdict(list)
                for param_change in semantic['parameters_changed']:
                    key = (param_change['track'], param_change['plugin'])
                    by_track_plugin[key].append(param_change)

                for (track_name, plugin_name), param_changes in by_track_plugin.items():
                    print(f"\n   Track: {track_name}")
                    print(f"   Plugin: {plugin_name}")
                    for param_change in param_changes[:20]:
                        param_name = param_change['parameter']
                        change_type = param_change.get('change', 'changed')
                        print(f"      • {param_name} {change_type}")
                    if len(param_changes) > 20:
                        print(f"      ... and {len(param_changes) - 20} more")

        # Show key differences
        if comparison['differences']['structural']:
            print(f"\n{'=' * 70}")
            print("Structural Changes (first 10)")
            print(f"{'=' * 70}")
            for i, diff in enumerate(comparison['differences']['structural'][:10], 1):
                print(f"{i}. {diff['element_type']} at {diff['path'][:60]}")
                print(f"   Count: {diff['file1_count']} → {diff['file2_count']}")

        if comparison['differences']['content']:
            print(f"\n{'=' * 70}")
            print("Content Changes (first 10)")
            print(f"{'=' * 70}")
            for i, diff in enumerate(comparison['differences']['content'][:10], 1):
                print(f"{i}. {diff.get('path', 'N/A')[:60]}")
                if 'attribute' in diff:
                    print(f"   {diff['attribute']}: {diff.get('file1_value', 'N/A')[:40]} → {diff.get('file2_value', 'N/A')[:40]}")

    def _print_semantic_comparison(self, comparison: Dict[str, Any]):
        """Print only semantic changes in simple format."""
        semantic = comparison.get('semantic_changes', {})

        for track_name in semantic.get('tracks_added', []):
            print(f"Added track: {track_name}")

        for track_name in semantic.get('tracks_removed', []):
            print(f"Removed track: {track_name}")

        if semantic.get('tempo_changed'):
            tempo = semantic['tempo_changed']
            print(f"Changed tempo: {tempo['from']} → {tempo['to']}")

        for plugin_change in semantic.get('plugins_added', []):
            print(f"Added plugin: {plugin_change['plugin']} on track '{plugin_change['track']}'")

        for plugin_change in semantic.get('plugins_removed', []):
            print(f"Removed plugin: {plugin_change['plugin']} from track '{plugin_change['track']}'")

        for param_change in semantic.get('parameters_changed', []):
            param_name = param_change['parameter']
            plugin_name = param_change['plugin']
            track_name = param_change['track']
            change_type = param_change.get('change', 'changed')
            print(f"Changed parameter: {param_name} ({plugin_name} on '{track_name}') {change_type}")


def main():
    parser = argparse.ArgumentParser(
        description='Smart comparison of .als files using schema')
    parser.add_argument('file1', help='First .als file')
    parser.add_argument('file2', help='Second .als file')
    parser.add_argument('--schema', default='12/schema.json',
                       help='Schema file path (relative to script directory)')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--semantic-only', '-s', action='store_true',
                       help='Show only semantic changes (simple list format)')
    parser.add_argument('--simple', action='store_true',
                       help='Alias for --semantic-only (simple list format)')

    args = parser.parse_args()

    file1 = Path(args.file1)
    file2 = Path(args.file2)

    if not file1.exists() or not file2.exists():
        print("Error: One or both files do not exist", file=sys.stderr)
        sys.exit(1)

    # Resolve schema path relative to package directory
    if args.schema:
        package_dir = Path(__file__).parent
        schema_path = package_dir / args.schema
    else:
        # Default to 12/schema.json in package directory
        package_dir = Path(__file__).parent
        schema_path = package_dir / '12' / 'schema.json'
    comparator = SmartALSComparator(schema_path)

    print("Comparing files...")
    comparison = comparator.compare(file1, file2)

    if args.json or args.output:
        output = json.dumps(comparison, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
        else:
            print(output)
    else:
        semantic_only = args.semantic_only or args.simple
        comparator.print_comparison(comparison, semantic_only=semantic_only)


if __name__ == '__main__':
    main()

