# -*- coding: utf-8 -*-
"""
Software Enumeration Plugin for NFA.

This plugin generates a report of installed software on Windows and Linux hosts
based on Nessus plugin outputs:
- Plugin ID 20811: Microsoft Windows Installed Software Enumeration (credentialed check)
- Plugin ID 22869: Unix Installed Software Enumeration (credentialed check)
"""

from typing import Dict, List, Any, Optional
import re
from nessus_file_analyzer.plugins import NFAPlugin, PluginMetadata


class SoftwareEnumerationPlugin(NFAPlugin):
    """Plugin for generating software inventory reports from Nessus scans."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Software Enumeration",
            id="software_enumeration",
            version="0.1.0",
            description="Generate inventory of installed software on Windows and Linux hosts",
            author="NFA Plugin Examples",
            plugin_ids=[20811, 22869]
        )

    def get_enabled_setting_key(self) -> str:
        return "plugin_software_enumeration_enabled"

    def get_additional_settings(self) -> List[Dict[str, Any]]:
        return [
            {
                'type': 'checkbox',
                'key': 'plugin_software_enumeration_group_by_software',
                'label': 'Group by software name',
                'default': False,
                'tooltip': 'When enabled, groups results by software name showing all hosts where it is installed'
            }
        ]

    def process_host_data(self, host_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract software inventory from a single host.

        Args:
            host_data: Host information including plugin outputs

        Returns:
            Dictionary with software inventory or None if no data
        """
        software_list = []

        # Extract host identification fields (matching vulnerabilities enumeration)
        report_host_name = host_data.get('report_host_name', '')
        resolved_hostname = host_data.get('resolved_hostname', '')
        hostname = host_data.get('hostname', '')
        ip = host_data.get('ip', '')
        fqdn = host_data.get('fqdn', '')
        os_info = host_data.get('os', '')
        scan_start_time = host_data.get('scan_start_time')  # Datetime object from nfr.host.host_time_start()
        scan_end_time = host_data.get('scan_end_time')  # Datetime object from nfr.host.host_time_end()
        plugins = host_data.get('plugins', [])

        # Determine if this is a Windows or Unix/Linux/macOS system
        is_windows = 'windows' in os_info.lower()
        is_unix_like = any(os_type in os_info.lower() for os_type in ['linux', 'unix', 'macos', 'mac os', 'darwin', 'bsd'])

        # Process plugins (now a list) to find software enumeration plugins
        for plugin_data in plugins:
            plugin_id = plugin_data.get('plugin_id', 0)

            # Check for Windows software (Plugin ID 20811) - only for Windows systems
            if is_windows and plugin_id == 20811:
                plugin_output = plugin_data.get('plugin_output', '')
                software_list.extend(self._parse_windows_software(plugin_output))

            # Check for Unix/Linux/macOS software (Plugin ID 22869) - only for non-Windows systems
            elif is_unix_like and plugin_id == 22869:
                plugin_output = plugin_data.get('plugin_output', '')
                software_list.extend(self._parse_unix_software(plugin_output))

        if not software_list:
            return None

        return {
            'report_host_name': report_host_name,
            'resolved_hostname': resolved_hostname,
            'hostname': hostname,  # Keep for backward compatibility
            'ip': ip,
            'fqdn': fqdn,
            'os': os_info,
            'scan_start_time': scan_start_time,
            'scan_end_time': scan_end_time,
            'software': software_list
        }

    def _parse_windows_software(self, plugin_output: str) -> List[Dict[str, str]]:
        """
        Parse Windows software from plugin 20811 output.

        The output format is typically:
        The following software are installed on the remote host :

        Software Name  [version X.X.X]  [installed on YYYY/MM/DD]

        Args:
            plugin_output: Raw plugin output text

        Returns:
            List of dictionaries with software info
        """
        software_list = []

        # Split by lines and skip first 3 lines (header)
        lines = plugin_output.split('\n')
        skip_count = 0

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip header lines (first 3 non-empty lines)
            if skip_count < 3:
                skip_count += 1
                continue

            # Extract version from [version X.X.X] pattern
            version = 'N/A'
            version_match = re.search(r'\[version\s+([^\]]+)\]', line)
            if version_match:
                version = version_match.group(1).strip()
                # Remove version part from line
                line = line[:version_match.start()].strip() + line[version_match.end():].strip()

            # Extract installation date from [installed on YYYY/MM/DD] pattern
            installed_on = ''
            installed_match = re.search(r'\[installed on\s+([^\]]+)\]', line)
            if installed_match:
                installed_on = installed_match.group(1).strip()
                # Remove installed on part from line
                line = line[:installed_match.start()].strip()

            # What's left is the software name
            name = line.strip()
            if name:
                software_list.append({
                    'name': name,
                    'version': version,
                    'platform': 'Windows',
                    'source': '',
                    'architecture': '',
                    'description': '',
                    'installed_on': installed_on,
                    'plugin_id': '20811'
                })

        return software_list

    def _parse_unix_software(self, plugin_output: str) -> List[Dict[str, str]]:
        """
        Parse Unix/Linux software from plugin 22869 output.

        The output format varies by distribution:
        - Debian/Ubuntu: "  ii   package  version  arch  description"
        - Other: "package version" or "package version (source)"

        Args:
            plugin_output: Raw plugin output text

        Returns:
            List of dictionaries with software info
        """
        software_list = []

        # Split by lines
        lines = plugin_output.split('\n')
        skip_count = 0

        for line in lines:
            # Don't strip yet - we need to check for leading spaces
            line = line.rstrip()

            # Skip empty lines and comments
            if not line or line.strip().startswith('#'):
                continue

            # Skip header lines
            stripped_line = line.strip()
            if skip_count < 2 and (stripped_line.startswith('Here is') or stripped_line.startswith('The following') or stripped_line.endswith(':')):
                skip_count += 1
                continue

            # Check for Debian/Ubuntu dpkg format: "  ii/rc   package  version  arch  description"
            if line.startswith('  ii') or line.startswith('  rc'):
                # Remove the "  ii" or "  rc" prefix
                line = line[4:].lstrip()

                # Split by multiple spaces (2 or more) to separate fields
                parts = re.split(r'  +', line, maxsplit=3)

                if len(parts) >= 4:
                    # Full format with all fields
                    name = parts[0].strip()
                    version = parts[1].strip()
                    architecture = parts[2].strip()
                    description = parts[3].strip()
                elif len(parts) == 3:
                    # Missing description
                    name = parts[0].strip()
                    version = parts[1].strip()
                    architecture = parts[2].strip()
                    description = ''
                elif len(parts) == 2:
                    # Missing architecture and description
                    name = parts[0].strip()
                    version = parts[1].strip()
                    architecture = ''
                    description = ''
                else:
                    # Only package name
                    name = parts[0].strip() if parts else line.strip()
                    version = 'N/A'
                    architecture = ''
                    description = ''

                if name:
                    software_list.append({
                        'name': name,
                        'version': version,
                        'platform': 'Unix/Linux',
                        'source': '',
                        'architecture': architecture,
                        'description': description,
                        'installed_on': '',
                        'plugin_id': '22869'
                    })
                continue

            # Handle non-Debian format (macOS, other Unix)
            line = stripped_line

            # Extract source information (e.g., "homebrew managed")
            source = ''
            if '(' in line and line.endswith(')'):
                # Extract source from parentheses
                match_source = re.search(r'\(([^)]+)\)$', line)
                if match_source:
                    source = match_source.group(1)
                    # Remove the source part from line
                    line = line[:match_source.start()].strip()

            # Parse software with version
            # Pattern handles various version formats:
            # - Standard: "Find My 4.0", "aom 3.12.1", "ffmpeg 7.1.1_3"
            # - Letter prefix: "x264 r3108"
            # - Letter suffix: "jpeg 9f"
            # Version must start with letter or digit and can contain dots, underscores, dashes
            match = re.match(r'^(.+?)\s+([a-zA-Z]?[0-9]+[a-zA-Z0-9._-]*)$', line)
            if match:
                name = match.group(1).strip()
                version = match.group(2).strip()
                software_list.append({
                    'name': name,
                    'version': version,
                    'platform': 'Unix/Linux',
                    'source': source,
                    'architecture': '',
                    'description': '',
                    'installed_on': '',
                    'plugin_id': '22869'
                })
            elif line:
                # If no version pattern matched, treat whole line as package name
                software_list.append({
                    'name': line,
                    'version': 'N/A',
                    'platform': 'Unix/Linux',
                    'source': source,
                    'architecture': '',
                    'description': '',
                    'installed_on': '',
                    'plugin_id': '22869'
                })

        return software_list

    def generate_report(self, workbook, processed_data: List[Dict[str, Any]],
                       parsing_settings: Dict[str, Any]) -> None:
        """
        Generate the Software Inventory Excel worksheet.

        Args:
            workbook: xlsxwriter.Workbook object
            processed_data: List of processed host data
            parsing_settings: User settings from UI
        """
        group_by_software = parsing_settings.get('plugin_software_enumeration_group_by_software', False)

        # Create worksheet
        worksheet = workbook.add_worksheet('software')

        # Define formats (matching vulnerabilities report style)
        cell_format_bold = workbook.add_format({"bold": True})
        worksheet.set_row(0, None, cell_format_bold)

        # Define cell formats for specific columns
        text_format = workbook.add_format({'num_format': '@'})  # Text format
        number_format = workbook.add_format({'num_format': '0'})  # Number format

        if group_by_software:
            # Group by software name
            self._generate_grouped_report(worksheet, processed_data, text_format, number_format)
        else:
            # List by host
            self._generate_host_report(worksheet, processed_data, text_format, number_format, workbook)

    def _generate_host_report(self, worksheet, processed_data, text_format, number_format, workbook):
        """Generate report grouped by host."""
        # Define datetime format for scan start/end timestamps
        datetime_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})

        # Set column widths for host-based report (matching vulnerabilities enumeration)
        worksheet.set_column('A:A', 18)  # Target
        worksheet.set_column('B:B', 18)  # Hostname
        worksheet.set_column('C:C', 18)  # FQDN
        worksheet.set_column('D:D', 18)  # IP
        worksheet.set_column('E:E', 20)  # Scan started
        worksheet.set_column('F:F', 20)  # Scan ended
        worksheet.set_column('G:G', 20)  # OS
        worksheet.set_column('H:H', 50)  # Software Name
        worksheet.set_column('I:I', 20, text_format)  # Software Version - text format
        worksheet.set_column('J:J', 12)  # Platform
        worksheet.set_column('K:K', 20)  # Software Source
        worksheet.set_column('L:L', 12)  # Architecture
        worksheet.set_column('M:M', 60)  # Software Description
        worksheet.set_column('N:N', 14)  # Installed on
        worksheet.set_column('O:O', 10, number_format)  # Plugin ID - number format

        # Write headers (matching vulnerabilities enumeration + scan timestamps)
        headers = ['Target', 'Hostname', 'FQDN', 'IP', 'Scan started', 'Scan ended', 'OS', 'Software Name', 'Software Version', 'Platform', 'Software Source', 'Architecture', 'Software Description', 'Installed on', 'Plugin ID']

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Freeze first row
        worksheet.freeze_panes(1, 0)

        # Write data
        row = 1
        for host in processed_data:
            # Extract host identification fields (matching vulnerabilities enumeration)
            report_host_name = host.get('report_host_name', '')
            resolved_hostname = host.get('resolved_hostname', '')
            fqdn = host.get('fqdn', '')
            ip = host.get('ip', '')
            os_info = host.get('os', '')
            scan_start_time = host.get('scan_start_time')  # Datetime object
            scan_end_time = host.get('scan_end_time')  # Datetime object

            for software in host['software']:
                col = 0
                # Target, Hostname, FQDN, IP (matching vulnerabilities enumeration)
                worksheet.write(row, col, report_host_name); col += 1  # Target
                worksheet.write(row, col, resolved_hostname); col += 1  # Hostname
                worksheet.write(row, col, fqdn); col += 1  # FQDN
                worksheet.write(row, col, ip); col += 1  # IP

                # Scan started - write as datetime (matching Standard report - hosts)
                if scan_start_time is not None:
                    worksheet.write_datetime(row, col, scan_start_time, datetime_format)
                else:
                    worksheet.write_blank(row, col, None)
                col += 1

                # Scan ended - write as datetime (matching Standard report - hosts)
                if scan_end_time is not None:
                    worksheet.write_datetime(row, col, scan_end_time, datetime_format)
                else:
                    worksheet.write_blank(row, col, None)
                col += 1

                worksheet.write(row, col, os_info); col += 1  # OS

                worksheet.write(row, col, software['name']); col += 1  # Software Name
                worksheet.write(row, col, software['version'], text_format); col += 1  # Software Version
                worksheet.write(row, col, software['platform']); col += 1  # Platform
                worksheet.write(row, col, software.get('source', '')); col += 1  # Software Source
                worksheet.write(row, col, software.get('architecture', '')); col += 1  # Architecture
                worksheet.write(row, col, software.get('description', '')); col += 1  # Software Description
                worksheet.write(row, col, software.get('installed_on', '')); col += 1  # Installed on

                # Plugin ID as number
                plugin_id = software.get('plugin_id', '')
                if plugin_id:
                    worksheet.write_number(row, col, int(plugin_id), number_format)
                else:
                    worksheet.write(row, col, '')
                col += 1

                row += 1

        # Apply autofilter
        worksheet.autofilter(0, 0, row - 1, len(headers) - 1)

        # Ignore "Number Stored as Text" warning for Version column (column I, index 8)
        if row > 1:
            worksheet.ignore_errors({'number_stored_as_text': f'I2:I{row}'})

    def _generate_grouped_report(self, worksheet, processed_data, text_format, number_format):
        """Generate report grouped by software name."""
        # Set column widths for grouped report
        worksheet.set_column('A:A', 50)  # Software Name
        worksheet.set_column('B:B', 12)  # Platform
        worksheet.set_column('C:C', 25, text_format)  # Software Versions - text format
        worksheet.set_column('D:D', 20)  # Software Source
        worksheet.set_column('E:E', 12)  # Architecture
        worksheet.set_column('F:F', 60)  # Software Description
        worksheet.set_column('G:G', 14)  # Installed on
        worksheet.set_column('H:H', 10, number_format)  # Plugin ID - number format
        worksheet.set_column('I:I', 12)  # Host Count
        worksheet.set_column('J:J', 60)  # Installed On (Hosts)

        # Aggregate software across all hosts
        software_map = {}

        for host in processed_data:
            hostname = host['hostname']
            ip = host['ip']

            for software in host['software']:
                key = software['name']
                if key not in software_map:
                    software_map[key] = {
                        'name': software['name'],
                        'versions': set(),
                        'platforms': set(),
                        'sources': set(),
                        'architectures': set(),
                        'descriptions': set(),
                        'installed_on_dates': set(),
                        'plugin_ids': set(),
                        'hosts': []
                    }

                software_map[key]['versions'].add(software['version'])
                software_map[key]['platforms'].add(software['platform'])
                software_map[key]['hosts'].append(f"{hostname} ({ip})")
                if software.get('source'):
                    software_map[key]['sources'].add(software['source'])
                if software.get('architecture'):
                    software_map[key]['architectures'].add(software['architecture'])
                if software.get('description'):
                    software_map[key]['descriptions'].add(software['description'])
                if software.get('installed_on'):
                    software_map[key]['installed_on_dates'].add(software['installed_on'])
                if software.get('plugin_id'):
                    software_map[key]['plugin_ids'].add(software['plugin_id'])

        # Write headers
        headers = ['Software Name', 'Platform', 'Software Versions', 'Software Source', 'Architecture', 'Software Description', 'Installed on', 'Plugin ID', 'Host Count', 'Installed On (Hosts)']

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Freeze first row
        worksheet.freeze_panes(1, 0)

        # Write data
        row = 1
        for software_name in sorted(software_map.keys()):
            software = software_map[software_name]

            worksheet.write(row, 0, software['name'])

            platforms_str = ', '.join(sorted(software['platforms']))
            worksheet.write(row, 1, platforms_str)

            versions_str = ', '.join(sorted(software['versions']))
            worksheet.write(row, 2, versions_str, text_format)

            sources_str = ', '.join(sorted(software['sources'])) if software['sources'] else ''
            worksheet.write(row, 3, sources_str)

            architectures_str = ', '.join(sorted(software['architectures'])) if software['architectures'] else ''
            worksheet.write(row, 4, architectures_str)

            descriptions_str = ', '.join(sorted(software['descriptions'])) if software['descriptions'] else ''
            worksheet.write(row, 5, descriptions_str)

            installed_on_str = ', '.join(sorted(software['installed_on_dates'])) if software['installed_on_dates'] else ''
            worksheet.write(row, 6, installed_on_str)

            # Plugin IDs - if single ID, write as number; if multiple, write as text
            if software['plugin_ids']:
                plugin_ids_list = sorted(software['plugin_ids'])
                if len(plugin_ids_list) == 1:
                    worksheet.write_number(row, 7, int(plugin_ids_list[0]), number_format)
                else:
                    plugin_ids_str = ', '.join(plugin_ids_list)
                    worksheet.write(row, 7, plugin_ids_str)
            else:
                worksheet.write(row, 7, '')

            worksheet.write(row, 8, len(software['hosts']))
            worksheet.write(row, 9, ', '.join(software['hosts']))

            row += 1

        # Apply autofilter
        worksheet.autofilter(0, 0, row - 1, len(headers) - 1)

        # Ignore "Number Stored as Text" warning for Versions column (column C, index 2)
        if row > 1:
            worksheet.ignore_errors({'number_stored_as_text': f'C2:C{row}'})
