# Quick Start Guide - Installing SUMO

## SUMO is not currently installed on your system. Follow these steps:

### Option 1: Install SUMO on Windows (Recommended)

1. **Download SUMO:**
   - Go to: https://sumo.dlr.de/docs/Downloads.php
   - Download the Windows installer (e.g., `sumo-win64-1.20.0.msi` or latest version)

2. **Install SUMO:**
   - Run the installer
   - Default installation path: `C:\Program Files (x86)\Eclipse\Sumo`
   - Make sure to check "Add to PATH" during installation (if available)

3. **Set Environment Variables (After Installation):**
   Open PowerShell as Administrator and run:
   ```powershell
   [Environment]::SetEnvironmentVariable("SUMO_HOME", "C:\Program Files (x86)\Eclipse\Sumo", "User")
   ```
   
   Or if installed in Program Files (without x86):
   ```powershell
   [Environment]::SetEnvironmentVariable("SUMO_HOME", "C:\Program Files\Eclipse\Sumo", "User")
   ```

4. **Restart your terminal/VS Code** to apply the changes

5. **Verify Installation:**
   ```powershell
   $env:SUMO_HOME
   sumo --version
   ```

### Option 2: Use Portable SUMO (No Installation Required)

1. Download SUMO portable version from the website
2. Extract to a folder (e.g., `C:\Sumo`)
3. Set SUMO_HOME for current session:
   ```powershell
   $env:SUMO_HOME = "C:\Sumo"
   $env:Path += ";C:\Sumo\bin"
   ```

### After SUMO is Installed:

Run the simulation with:
```powershell
cd C:\Users\vaish\trafcon
python emergency_vehicle_simulation.py --gui
```

## Alternative: Try Without Full Installation

If you want to test the code structure without SUMO, I can create a mock simulation that demonstrates the logic without the actual SUMO backend.

Would you like me to:
1. Wait for you to install SUMO and then help you run it?
2. Create a mock version to test the Python logic?
3. Create a video tutorial document?
