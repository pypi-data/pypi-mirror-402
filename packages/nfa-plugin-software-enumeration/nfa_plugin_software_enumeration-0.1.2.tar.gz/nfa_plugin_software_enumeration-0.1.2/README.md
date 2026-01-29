# Software Enumeration

The *Software Enumeration* is a report plugin for **[LimberDuck] [NFA (nessus file analyzer)]** to generate report from software installed on remote systems scanned with *Tenable Nessus* or *Tenable Security Center*.

List of installed software is based on Nessus plugin outputs listed below:
- Plugin ID [20811](https://www.tenable.com/plugins/nessus/20811): Microsoft Windows Installed Software Enumeration (credentialed check)
- Plugin ID [22869](https://www.tenable.com/plugins/nessus/22869): Software Enumeration (SSH)


> [!CAUTION]
> The *Software Enumeration* report plugin for **[LimberDuck] [NFA (nessus file analyzer)]** has been tested on results reported for Operating Systems:
> - Microsoft Windows 10 (Nessus Plugin ID 20811)
> - Ubuntu 24.04 (Nessus Plugin ID 22869)
> - macOS 15.6 (Nessus Plugin ID 22869)
>
> If you find any issues or have suggestions for other Operating Systems, please open an [issue](https://github.com/LimberDuck/nfa-plugin-software-enumeration/issues) on the GitHub repository.


> [!IMPORTANT]
> The target hosts must be scanned with credentialed checks enabled for Plugin IDs 20811 and/or 22869 to appear in the scan results.

## Features

- **Platform Support**: Windows, Linux, Unix, macOS, etc. (all supported by Nessus Plugin ID: 20811 and 22869)
- **Two View Modes**: List by host or group by software name
- **Version Information**: Software version in dedicated column
- **Source Tracking**: For Unix/Linux/macOS packages (e.g., "homebrew managed")
- **Installation Dates**: Captured for Windows software when available
- **Plugin ID Tracking**: Shows which Nessus plugin (20811 or 22869) provided the data
- **Spreadsheet Formatting**: Styling matching NFA's standard reports (clean design, bold headers, no borders, frozen first row, autofilter)
- **Advanced Version Parsing**: Handles various version formats including:
  - Standard versions: `2.4.41`, `8.2p1`, `3.12.1`
  - Letter prefixes: `r3108` (e.g., x264 r3108)
  - Letter suffixes: `9f` (e.g., jpeg 9f)
  - Complex versions: `7.1.1_3` (e.g., ffmpeg 7.1.1_3)

## Installation

> [!IMPORTANT]
> *Software Enumeration* report plugin `v0.1.0` works with **LimberDuck NFA (nessus file analyzer)** `v0.12.0` or newer.

This plugin is automatically installed with **LimberDuck NFA (nessus file analyzer)** `v0.12.0` or newer. 

If you already have **LimberDuck NFA (nessus file analyzer)** installed in `v0.12.0` or newer and want to manually install newer version of *Software Enumeration* NFA plugin, run:

```bash
pip install nfa-plugin-software-enumeration
```

> [!NOTE]
> If you want to make some changes to the plugin code and test them locally, clone the repository and install it in development mode:
>
>  ```bash
>  cd nfa-plugin-software-enumeration
>  pip install -e .
>  ```


## Usage

1. Open **LimberDuck NFA (nessus file analyzer)**.
2. Navigate to the **Advanced reports** tab in the Settings section.
3. Find **Software Enumeration** report on the list.
4. Check **Enable**.
5. (Optional) Configure plugin option:
   - **Group by software name**: When enabled, groups results by software name showing all hosts where it is installed
6. Select your `.nessus` files and click **Start** button.

If selected `.nessus` files contain relevant data from Plugin ID 20811 and/or 22869, generated report will include worksheet named "software". See example output below.

## Example Output

### By Host (Default)

| Target               | Hostname    | FQDN                 | IP       | Scan started        | Scan ended          | OS                  | Software Name                             | Software Version | Platform   | Software Source  | Architecture | Software Description                          | Installed on | Plugin ID |
|----------------------|-------------|----------------------|----------|---------------------|---------------------|---------------------|-------------------------------------------|------------------|------------|------------------|--------------|-----------------------------------------------|--------------|-----------|
| server01.example.com | server01    | server01.example.com | 10.0.0.1 | 2025-12-08 10:00:00 | 2025-12-08 10:15:00 | Ubuntu 22.04        | openssh-server                            | 8.2p1-4          | Unix/Linux | apt              |              |                                               |              | 22869     |
| server01.example.com | server01    | server01.example.com | 10.0.0.1 | 2025-12-08 10:00:00 | 2025-12-08 10:15:00 | Ubuntu 22.04        | apache2                                   | 2.4.41           | Unix/Linux | apt              |              |                                               |              | 22869     |
| workstation.local    | workstation | workstation.local    | 10.0.0.5 | 2025-12-08 11:00:00 | 2025-12-08 11:20:00 | macOS Ventura       | ffmpeg                                    | 7.1.1_3          | Unix/Linux | homebrew managed |              |                                               |              | 22869     |
| workstation.local    | workstation | workstation.local    | 10.0.0.5 | 2025-12-08 11:00:00 | 2025-12-08 11:20:00 | macOS Ventura       | jpeg                                      | 9f               | Unix/Linux | homebrew managed |              |                                               |              | 22869     |
| 10.0.0.2             | server02    | server02.corp.local  | 10.0.0.2 | 2025-12-08 09:30:00 | 2025-12-08 09:50:00 | Windows Server 2019 | Microsoft Office Professional Plus 2019   | 16.0.10337.20039 | Windows    |                  |              |                                               | 2025/11/26   | 20811     |
| localhost            | ubuntu      |                      | 127.0.0.1| 2025-06-28 07:07:13 | 2025-06-28 07:23:02 | Linux Kernel 6.8.0-59-generic on Ubuntu 24.04 | accountsservice | 23.13.9-2ubuntu6 | Unix/Linux |                  | arm64        | query and manipulate user account information |              | 22869     |


### Grouped by Software name

| Software Name                           | Platform   | Software Versions | Software Source  | Architecture | Software Description | Installed on | Plugin ID | Host Count | Installed On (Hosts)                                                |
|-----------------------------------------|------------|-------------------|------------------|--------------|----------------------|--------------|-----------|------------|---------------------------------------------------------------------|
| ffmpeg                                  | Unix/Linux | 7.1.1_3           | homebrew managed |              |                      |              | 22869     | 1          | workstation.local                                                   |
| apache2                                 | Unix/Linux | 2.4.41, 2.4.43    |                  |              |                      |              | 22869     | 5          | server01 (10.0.0.1), server02 (10.0.0.2), server03 (10.0.0.3), ...  |
| Microsoft Office Professional Plus 2019 | Windows    | 16.0.10337.20039  |                  |              |                      | 2025/11/26   | 20811     | 3          | server02 (10.0.0.2), server03 (10.0.0.3), workstation01 (10.0.0.10) |
| accountsservice                         | Unix/Linux | 23.13.9-2ubuntu6. |                  | arm64        | query and manipulate user account information | | 22869 | 1  | ubuntu (127.0.0.1)                                                  |

## Technical Details

For Windows systems the Plugin ID 20811 is used:

- Detects "windows" in OS information
- Parses software with version from `[version X.X.X]`
- Extracts installation dates from `[installed on YYYY/MM/DD]`
- Skips first 3 header lines before parsing software list. 

Example Plugin ID 20811 output:

```

The following software are installed on the remote host :

7-Zip 24.09 (x64)  [version 24.09]
Microsoft Edge  [version 142.0.3595.94]  [installed on 2025/11/26]
```

For Linux/Unix-like systems the Plugin ID 22869 is used:

- Detects: e.g. Ubuntu, macOS
- Extracts source information from parentheses (e.g., `(homebrew managed)`)
- Handles various version formats with advanced regex patterns
- Skips first 3 header lines before parsing software list. 

Example Plugin ID 22869 outputs:

```

Here is the list of packages installed on the remote Mac OS X system :

  App Store 3.0
  Automator 2.10
  ...
  ffmpeg 7.1.1_3 (homebrew managed)
```

```

Here is the list of packages installed on the remote Debian Linux system :

  ii   accountsservice  23.13.9-2ubuntu6  arm64  query and manipulate user account information
  ii   acl  2.3.2-1build1.1  arm64  access control list - utilities
```


The Unix/Linux parser uses a regex pattern to handle diverse version formats:
- Pattern: `^(.+?)\s+([a-zA-Z]?[0-9]+[a-zA-Z0-9._-]*)$`
- Supports versions starting with letters (e.g., `r3108`, `v2.1.0`)
- Handles versions ending with letters (e.g., `9f`)
- Captures compound versions with dots, underscores, and dashes (e.g., `7.1.1_3`, `8.2p1-4`)

Spreadsheet Formatting

- **Version** column: Formatted as text to prevent Excel from misinterpreting versions as numbers.
- **Plugin ID** column: Formatted as number for proper sorting and filtering.
- **Scan started** and **Scan ended** columns: Formatted as datetime for accurate date handling.
- **First row**: Bold formatting and frozen for easy navigation.
- **Auto-filter**: Applied to all columns for quick data filtering.
- **Styling**: Matches the standard NFA's reports (clean design, bold headers, no borders, frozen first row, autofilter).

## Licence

GNU GPLv3: [LICENSE].


## Authors

[Damian Krawczyk] created [Software Enumeration] report plugin for **[LimberDuck] [NFA (nessus file analyzer)]**.

[Software Enumeration]: https://limberduck.org/en/latest/tools/nessus-file-analyzer/advanced-reports/software-enumeration/
[NFA (nessus file analyzer)]: https://limberduck.org/en/latest/tools/nessus-file-analyzer
[Damian Krawczyk]: https://damiankrawczyk.com
[LimberDuck]: https://limberduck.org
[CHANGELOG]: https://github.com/LimberDuck/nfa-plugin-software-enumeration/blob/master/CHANGELOG.md
[LICENSE]: https://github.com/LimberDuck/nfa-plugin-software-enumeration/blob/master/LICENSE
