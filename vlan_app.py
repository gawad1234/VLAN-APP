"""List virtual VLAN adapters on Windows.

This script queries Windows networking stack (via PowerShell) to find network
adapters and any VLAN-related advanced properties configured on them.

Usage:
  python vlan_app.py           # CLI list
  python vlan_app.py --gui     # Simple GUI viewer (tkinter)

Notes:
  - This tool runs on Windows only.
  - It uses PowerShell cmdlets (Get-NetAdapter, Get-NetAdapterAdvancedProperty).
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional


def run_powershell_command(cmd: str) -> str:
    # Use -NoProfile to avoid loading user profiles, making it more deterministic.
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            f"PowerShell command failed (exit {completed.returncode}):\n"
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )

    return completed.stdout


def _maybe_parse_json(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return []

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Sometimes PowerShell prints warnings/multiline headers; try to find JSON start.
        idx = raw.find("{")
        if idx != -1:
            return json.loads(raw[idx:])
        raise


def get_net_adapters() -> List[Dict[str, Any]]:
    cmd = (
        "Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,MacAddress,InterfaceIndex | "
        "ConvertTo-Json -Depth 4"
    )
    out = run_powershell_command(cmd)
    data = _maybe_parse_json(out)
    if isinstance(data, dict):
        return [data]
    return data


def get_vlan_properties() -> List[Dict[str, Any]]:
    cmd = (
        "Get-NetAdapterAdvancedProperty | "
        "Where-Object { $_.DisplayName -match 'Vlan|VLAN|vlan' -or $_.RegistryKeyword -match 'Vlan|VLAN|vlan' } | "
        "Select-Object Name,DisplayName,RegistryKeyword,RegistryValue,InterfaceIndex | "
        "ConvertTo-Json -Depth 4"
    )
    out = run_powershell_command(cmd)
    data = _maybe_parse_json(out)
    if isinstance(data, dict):
        return [data]
    return data


def _normalize_string(value: Optional[str]) -> str:
    return (value or "").strip() or "(none)"


def format_adapter_rows(adapters: List[Dict[str, Any]], vlan_props: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    # Build a map from InterfaceIndex to VLAN property summaries
    vlan_map: Dict[Any, List[str]] = {}
    for prop in vlan_props:
        idx = prop.get("InterfaceIndex")
        if idx is None:
            idx = prop.get("Name")
        summary = f"{_normalize_string(prop.get('DisplayName'))}={_normalize_string(prop.get('RegistryValue'))}"
        vlan_map.setdefault(idx, []).append(summary)

    rows: List[Dict[str, str]] = []
    for adapter in adapters:
        idx = adapter.get("InterfaceIndex")
        vlan_list = vlan_map.get(idx, [])
        rows.append(
            {
                "Name": _normalize_string(adapter.get("Name")),
                "Description": _normalize_string(adapter.get("InterfaceDescription")),
                "Status": _normalize_string(adapter.get("Status")),
                "MAC": _normalize_string(adapter.get("MacAddress")),
                "VLAN Properties": "; ".join(vlan_list) or "(none found)",
            }
        )

    return rows


def print_table(rows: List[Dict[str, str]]) -> None:
    if not rows:
        print("No network adapter information found.")
        return

    headers = list(rows[0].keys())
    col_widths = {h: len(h) for h in headers}
    for row in rows:
        for h, v in row.items():
            col_widths[h] = max(col_widths[h], len(v))

    sep = "  "
    header_line = sep.join(h.ljust(col_widths[h]) for h in headers)
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        line = sep.join(row[h].ljust(col_widths[h]) for h in headers)
        print(line)


def main(cli_args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="List virtual VLAN adapters on Windows.")
    parser.add_argument("--gui", action="store_true", help="Open a simple GUI window (tkinter)")
    args = parser.parse_args(cli_args)

    if platform.system() != "Windows":
        print("This tool is designed for Windows and uses PowerShell cmdlets.")
        return 1

    try:
        adapters = get_net_adapters()
        vlan_props = get_vlan_properties()
    except Exception as e:
        print(f"Failed to query adapter details: {e}")
        return 1

    rows = format_adapter_rows(adapters, vlan_props)

    if args.gui:
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            from datetime import datetime

            columns = ["Name", "Description", "Status", "MAC", "VLAN Properties"]

            def build_tree(parent: tk.Widget) -> ttk.Treeview:
                tree = ttk.Treeview(parent, columns=columns, show="headings")
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, anchor="w", width=160)
                return tree

            def refresh() -> None:
                try:
                    adapters = get_net_adapters()
                    vlan_props = get_vlan_properties()
                    rows = format_adapter_rows(adapters, vlan_props)
                except Exception as e:
                    messagebox.showerror("Failed to refresh", f"Failed to query adapter details:\n{e}")
                    return

                for item in tree.get_children():
                    tree.delete(item)

                for row in rows:
                    tree.insert("", "end", values=[row.get(col, "") for col in columns])

                status_var.set(
                    f"Last updated {datetime.now():%H:%M:%S} — {len(rows)} adapters"
                )

            root = tk.Tk()
            root.title("VLAN Adapters")
            root.geometry("1000x420")

            toolbar = ttk.Frame(root)
            toolbar.pack(fill="x", padx=6, pady=6)

            refresh_btn = ttk.Button(toolbar, text="Refresh", command=refresh)
            refresh_btn.pack(side="left")

            close_btn = ttk.Button(toolbar, text="Close", command=root.destroy)
            close_btn.pack(side="left", padx=(6, 0))

            tree = build_tree(root)
            tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

            status_var = tk.StringVar(value="Ready")
            status = ttk.Label(root, textvariable=status_var, anchor="w")
            status.pack(fill="x", padx=6, pady=(0, 6))

            refresh()
            root.mainloop()
            return 0
        except Exception as e:
            print(f"Failed to launch GUI: {e}")
            return 1

    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
