# SUMO Emergency Vehicle Priority Simulation

This simulation demonstrates an intelligent traffic light system that gives priority to emergency vehicles at intersections while maintaining normal traffic flow.

## Overview

### System Features:
- **Normal Operation**: Traffic signals give 20 seconds of green light to each direction
- **Emergency Detection**: System detects emergency vehicles within 50 meters of the intersection
- **Priority Activation**: When detected, the signal changes to green for the emergency vehicle's direction
- **Extended Green Time**: Emergency vehicles get 25 seconds of green light (5 seconds more than normal)
- **Dedicated Lane**: Emergency vehicles use lane 2 (rightmost lane) exclusively
- **Automatic Recovery**: System returns to normal operation after the emergency vehicle passes

## Files Description

### 1. `intersection.net.xml`
Network definition file containing:
- 4-way intersection with traffic light at center
- 3 lanes per direction (lane 2 is the emergency lane)
- North, South, East, and West approaches
- Traffic light logic with phase definitions

### 2. `vehicles.rou.xml`
Route and vehicle definitions:
- **Normal vehicles**: Yellow passenger cars using lanes 0 and 1
- **Emergency vehicles**: Red emergency vehicles (ambulances) using lane 2
- Multiple emergency vehicles spawned at different times
- Normal traffic flows from all directions

### 3. `additional.add.xml`
Additional infrastructure:
- Induction loop detectors on all lanes
- Special detectors on emergency lanes (lane 2) for detection
- Data collection for analysis

### 4. `emergency_vehicle_simulation.py`
Main Python control script implementing:
- Emergency vehicle detection system
- Traffic light control logic
- Priority activation and deactivation
- Real-time monitoring and logging

### 5. `simulation.sumocfg`
Main SUMO configuration file that ties all components together

### 6. `gui-settings.xml`
Visual settings for the SUMO GUI interface

## Requirements

### Software:
- **SUMO** (Simulation of Urban MObility) - Version 1.8.0 or higher
- **Python** - Version 3.7 or higher
- **TraCI** library (included with SUMO)

### Installation:

#### Windows:
1. Download SUMO from: https://sumo.dlr.de/docs/Downloads.php
2. Install SUMO (default location: `C:\Program Files (x86)\Eclipse\Sumo`)
3. Set environment variable:
   ```powershell
   [Environment]::SetEnvironmentVariable("SUMO_HOME", "C:\Program Files (x86)\Eclipse\Sumo", "User")
   ```
4. Add to PATH:
   ```powershell
   $env:Path += ";C:\Program Files (x86)\Eclipse\Sumo\bin"
   ```

#### Linux:
```bash
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
export SUMO_HOME="/usr/share/sumo"
```

#### macOS:
```bash
brew install sumo
export SUMO_HOME="/usr/local/opt/sumo/share/sumo"
```

## How to Run

### Method 1: With GUI (Recommended for visualization)
```powershell
python emergency_vehicle_simulation.py --gui
```
or simply:
```powershell
python emergency_vehicle_simulation.py
```

### Method 2: Without GUI (Faster execution)
```powershell
python emergency_vehicle_simulation.py --no-gui
```

### Method 3: Run SUMO directly (without emergency vehicle priority)
```powershell
sumo-gui -c simulation.sumocfg
```

## Understanding the Simulation

### Traffic Light Phases:
1. **Phase 0**: North-South Green (20s normally, 25s for emergency)
2. **Phase 1**: North-South Yellow (3s)
3. **Phase 2**: East-West Green (20s normally, 25s for emergency)
4. **Phase 3**: East-West Yellow (3s)

### Emergency Vehicle Behavior:
1. Emergency vehicle spawns and travels in dedicated lane 2
2. Detector senses vehicle 50m before intersection
3. System activates priority:
   - Current phase switches to yellow (3s)
   - Emergency vehicle's direction gets green (25s)
4. Emergency vehicle crosses intersection
5. System returns to normal 20s cycle

### Emergency Vehicles in Simulation:
- `emergency_1`: Departs at 30s from North
- `emergency_2`: Departs at 120s from South
- `emergency_3`: Departs at 200s from East
- `emergency_4`: Departs at 300s from West
- `emergency_5`: Departs at 450s from North
- `emergency_6`: Departs at 600s from East

## Customization

### Modify Emergency Vehicle Count:
Edit `vehicles.rou.xml` and add more entries:
```xml
<vehicle id="emergency_7" type="emergency" route="route_N_S_2" depart="750" departLane="2" departSpeed="max" color="1,0,0"/>
```

### Change Signal Timings:
Edit `emergency_vehicle_simulation.py`:
```python
self.normal_phase_duration = 20  # Change normal duration
self.emergency_phase_duration = 25  # Change emergency duration
```

### Adjust Detection Distance:
Edit `emergency_vehicle_simulation.py`:
```python
self.detection_distance = 50  # Distance in meters
```

### Modify Traffic Density:
Edit `vehicles.rou.xml` and change probability values:
```xml
<flow id="flow_N_S_normal_0" ... probability="0.15"/>  <!-- Increase for more traffic -->
```

## Monitoring and Analysis

### Console Output:
The script provides real-time information:
- Emergency vehicle detection alerts
- Priority activation/deactivation
- Current traffic light phase
- Vehicle counts
- Simulation progress

### Output Files:
- `detector_output.xml`: Detector data for all vehicles
- Can be analyzed for traffic statistics

## Troubleshooting

### Issue: "SUMO_HOME not found"
**Solution**: Set the SUMO_HOME environment variable to your SUMO installation directory

### Issue: "Configuration file not found"
**Solution**: Ensure you're running the script from the directory containing all XML files

### Issue: No emergency vehicles appearing
**Solution**: Check that the simulation runs long enough (emergency vehicles spawn at different times)

### Issue: Traffic light not changing
**Solution**: Verify that TraCI connection is established and emergency vehicles are using lane 2

## Technical Details

### Lane Assignment:
- **Lane 0**: Normal traffic (leftmost)
- **Lane 1**: Normal traffic (middle)
- **Lane 2**: Emergency vehicles only (rightmost)

### Detection System:
- Uses induction loops at 50m before intersection
- Checks vehicle type for emergency classification
- Tracks processed vehicles to avoid duplicate activations

### Priority Logic:
1. Continuous monitoring for emergency vehicles
2. Distance-based detection (50m threshold)
3. Direction identification (NS or EW)
4. Safe phase transition (yellow light first if needed)
5. Extended green duration (25s vs 20s)
6. Automatic deactivation after passage

## Performance Notes

- Simulation runs at 10 Hz (step-length = 0.1s)
- Designed for 1 hour of simulation time (3600s)
- Can handle multiple emergency vehicles sequentially
- Emergency vehicles are prioritized by proximity

## Future Enhancements

Possible improvements:
1. Multi-intersection coordination
2. Predictive emergency vehicle routing
3. Dynamic green time based on queue length
4. Emergency vehicle convoy support
5. Integration with real-world traffic data
6. Mobile app notifications for drivers

## License

This simulation is provided as-is for educational and research purposes.

## Contact & Support

For issues or questions about this simulation:
1. Check SUMO documentation: https://sumo.dlr.de/docs/
2. SUMO mailing list: https://www.eclipse.org/lists/sumo-user
3. TraCI documentation: https://sumo.dlr.de/docs/TraCI.html

---

**Note**: This is a simulation and should not be used as the sole basis for real-world traffic control systems without proper validation and safety analysis.
