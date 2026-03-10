# VLAN-APP

A small Windows tool to list network adapters and any configured VLAN (virtual LAN) settings.

## 📌 What it does

- Uses PowerShell (`Get-NetAdapter` and `Get-NetAdapterAdvancedProperty`) to detect adapters
- Reports VLAN-related advanced properties (e.g., VLAN ID settings from NIC drivers)
- Can run in the terminal (CLI) or show a simple GUI window with `--gui`

## ▶️ Running (Windows)

### Python (optional)

If you have Python installed, you can run the included Python tool:

```powershell
python vlan_app.py
```

To open a simple GUI viewer:

```powershell
python vlan_app.py --gui
```

### PowerShell (no Python required)

If you do not have Python installed, use the PowerShell script:

```powershell
.\list-vlans.ps1
```

## 📄 Files

- `vlan_app.py` – main script

## 🛠 Notes

- This tool requires Windows and PowerShell (built into Windows).
- If nothing VLAN-related appears, your adapters may not expose VLAN IDs as advanced properties.
