#!/usr/bin/env python3
"""
SUMO Traffic Simulation with Emergency Vehicle Priority System

This script implements a traffic light control system that:
1. Runs normal traffic with 20-second green phases
2. Detects emergency vehicles approaching the intersection
3. Changes traffic light to green for emergency vehicle direction (25 seconds)
4. Returns to normal operation after emergency vehicle passes

Requirements:
- SUMO (Simulation of Urban MObility)
- Python 3.x
- traci library (comes with SUMO)
"""

import os
import sys
import traci
import time

# Set SUMO_HOME environment variable if not already set
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")


class EmergencyVehiclePriority:
    """Manages traffic light control for emergency vehicle priority"""
    
    def __init__(self, tl_id='center'):
        self.tl_id = tl_id
        self.normal_phase_duration = 5  # Normal green phase duration (5 seconds)
        self.emergency_phase_duration = 10  # Emergency green phase duration (10 seconds)
        self.yellow_duration = 2  # Yellow phase duration (reduced to 2s for faster switching)
        
        # Traffic light phase definitions
        # Phase indices: 0=NS_green, 1=NS_yellow, 2=EW_green, 3=EW_yellow
        self.PHASE_NS_GREEN = 0
        self.PHASE_NS_YELLOW = 1
        self.PHASE_EW_GREEN = 2
        self.PHASE_EW_YELLOW = 3
        
        # State tracking
        self.emergency_active = False
        self.emergency_vehicle_id = None
        self.emergency_direction = None
        self.emergency_start_time = 0
        self.processed_emergency_vehicles = set()
        
        # Detection zones (distance from intersection in meters)
        self.detection_distance = 50
        
    def get_vehicle_direction(self, vehicle_id):
        """Determine which direction (NS or EW) the vehicle is traveling"""
        try:
            road_id = traci.vehicle.getRoadID(vehicle_id)
            
            if 'north_in' in road_id or 'south_in' in road_id:
                return 'NS'
            elif 'east_in' in road_id or 'west_in' in road_id:
                return 'EW'
            else:
                return None
        except:
            return None
    
    def is_emergency_vehicle(self, vehicle_id):
        """Check if a vehicle is an emergency vehicle"""
        try:
            vehicle_type = traci.vehicle.getTypeID(vehicle_id)
            return vehicle_type == 'emergency'
        except:
            return False
    
    def get_approaching_emergency_vehicles(self):
        """Detect emergency vehicles approaching the intersection"""
        emergency_vehicles = []
        
        # Get all vehicles in simulation
        all_vehicles = traci.vehicle.getIDList()
        
        for veh_id in all_vehicles:
            # Skip if already processed
            if veh_id in self.processed_emergency_vehicles:
                continue
                
            # Check if it's an emergency vehicle
            if self.is_emergency_vehicle(veh_id):
                try:
                    road_id = traci.vehicle.getRoadID(veh_id)
                    
                    # Check if vehicle is on an incoming edge
                    if '_in' in road_id and 'center' not in road_id:
                        # Get distance to intersection
                        lane_pos = traci.vehicle.getLanePosition(veh_id)
                        lane_id = traci.vehicle.getLaneID(veh_id)
                        lane_length = traci.lane.getLength(lane_id)
                        
                        # Distance to intersection
                        distance_to_junction = lane_length - lane_pos
                        
                        # If within detection range
                        if distance_to_junction <= self.detection_distance:
                            direction = self.get_vehicle_direction(veh_id)
                            if direction:
                                emergency_vehicles.append({
                                    'id': veh_id,
                                    'direction': direction,
                                    'distance': distance_to_junction
                                })
                                print(f"[ALERT] Emergency vehicle detected: {veh_id} from {direction} direction, {distance_to_junction:.1f}m away")
                except:
                    continue
        
        return emergency_vehicles
    
    def activate_emergency_priority(self, vehicle_id, direction):
        """Activate emergency vehicle priority for the given direction"""
        print(f"\n{'='*60}")
        print(f"[PRIORITY] Emergency vehicle {vehicle_id} detected!")
        print(f"[PRIORITY] Direction: {direction}")
        print(f"[PRIORITY] Max duration: {self.emergency_phase_duration}s (or until vehicle passes)")
        print(f"[PRIORITY] ALL OTHER DIRECTIONS SET TO RED")
        print(f"{'='*60}\n")
        
        self.emergency_active = True
        self.emergency_vehicle_id = vehicle_id
        self.emergency_direction = direction
        self.emergency_start_time = traci.simulation.getTime()
        
        # Set traffic light: GREEN for emergency direction, RED for all others
        # Traffic light state format: 12 characters for 12 links (3 lanes x 4 directions)
        # Order: north_in (3), east_in (3), south_in (3), west_in (3)
        # G=green, r=red, y=yellow
        
        if direction == 'NS':
            # North-South GREEN, East-West RED
            # Format: NS(3) + EW(3) + NS(3) + EW(3) = 12 signals
            emergency_state = "GGGrrrGGGrrr"
            print(f"[SIGNAL] North-South: GREEN | East-West: RED")
            traci.trafficlight.setRedYellowGreenState(self.tl_id, emergency_state)
            traci.trafficlight.setPhaseDuration(self.tl_id, self.emergency_phase_duration)
                
        elif direction == 'EW':
            # East-West GREEN, North-South RED
            # Format: NS(3) + EW(3) + NS(3) + EW(3) = 12 signals
            emergency_state = "rrrGGGrrrGGG"
            print(f"[SIGNAL] East-West: GREEN | North-South: RED")
            traci.trafficlight.setRedYellowGreenState(self.tl_id, emergency_state)
            traci.trafficlight.setPhaseDuration(self.tl_id, self.emergency_phase_duration)
    
    def check_emergency_vehicle_passed(self):
        """Check if emergency vehicle has passed the intersection"""
        if not self.emergency_active:
            return False
        
        try:
            # Check if vehicle still exists in simulation
            if self.emergency_vehicle_id not in traci.vehicle.getIDList():
                print(f"[INFO] Emergency vehicle {self.emergency_vehicle_id} has left the simulation")
                return True
            
            # Check if vehicle has passed the intersection
            road_id = traci.vehicle.getRoadID(self.emergency_vehicle_id)
            
            # If vehicle is on outgoing edge, it has passed - IMMEDIATELY return to normal
            if '_out' in road_id or road_id == '':
                print(f"[INFO] Emergency vehicle {self.emergency_vehicle_id} has passed the intersection")
                return True
            
            # Safety timeout - if 10 seconds elapsed, assume vehicle passed
            current_time = traci.simulation.getTime()
            elapsed_time = current_time - self.emergency_start_time
            
            if elapsed_time >= 10:
                print(f"[TIMEOUT] Emergency priority timeout after {elapsed_time:.1f}s - resuming normal operation")
                return True
                
        except:
            return True
        
        return False
    
    def deactivate_emergency_priority(self):
        """Deactivate emergency priority and return to normal operation"""
        print(f"\n{'='*60}")
        print(f"[NORMAL] Emergency vehicle {self.emergency_vehicle_id} has passed")
        print(f"[NORMAL] Returning to normal traffic light operation")
        print(f"[NORMAL] Switching to opposite direction immediately")
        print(f"{'='*60}\n")
        
        # Mark vehicle as processed
        self.processed_emergency_vehicles.add(self.emergency_vehicle_id)
        
        # Store the emergency direction to switch to opposite
        last_emergency_direction = self.emergency_direction
        
        # Reset state
        self.emergency_active = False
        self.emergency_vehicle_id = None
        self.emergency_direction = None
        self.emergency_start_time = 0
        
        # Immediately switch to opposite direction to serve waiting vehicles
        # Use brief yellow (2s) then switch to green for opposite direction
        if last_emergency_direction == 'NS':
            # Was NS green, now give green to EW (opposite direction)
            yellow_state = "yyyrrryyyrrr"  # NS yellow, EW red (brief transition)
            green_state = "rrrGGGrrrGGG"   # EW green, NS red
            
            # Set yellow briefly
            traci.trafficlight.setRedYellowGreenState(self.tl_id, yellow_state)
            traci.trafficlight.setPhaseDuration(self.tl_id, 2)  # Short yellow
            
        elif last_emergency_direction == 'EW':
            # Was EW green, now give green to NS (opposite direction)
            yellow_state = "rrryyyrrryyy"  # EW yellow, NS red (brief transition)
            green_state = "GGGrrrGGGrrr"   # NS green, EW red
            
            # Set yellow briefly
            traci.trafficlight.setRedYellowGreenState(self.tl_id, yellow_state)
            traci.trafficlight.setPhaseDuration(self.tl_id, 2)  # Short yellow
    
    def run(self):
        """Main simulation loop"""
        print("\n" + "="*60)
        print("SUMO Emergency Vehicle Priority System")
        print("="*60)
        print(f"NORMAL OPERATION:")
        print(f"  - Green signal: {self.normal_phase_duration} seconds")
        print(f"  - Red signal: {self.normal_phase_duration} seconds (opposite direction green)")
        print(f"  - Yellow transition: {self.yellow_duration} seconds")
        print(f"EMERGENCY MODE:")
        print(f"  - Emergency vehicles arrive every 15 seconds")
        print(f"  - Priority duration: {self.emergency_phase_duration} seconds max")
        print(f"  - All other directions: RED")
        print(f"  - Returns to normal immediately after vehicle passes")
        print("="*60 + "\n")
        
        step = 0
        
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step += 1
            
            # Check if emergency vehicle has passed
            if self.emergency_active:
                if self.check_emergency_vehicle_passed():
                    self.deactivate_emergency_priority()
            
            # If no emergency is active, check for approaching emergency vehicles
            if not self.emergency_active:
                emergency_vehicles = self.get_approaching_emergency_vehicles()
                
                if emergency_vehicles:
                    # Prioritize closest emergency vehicle
                    closest = min(emergency_vehicles, key=lambda x: x['distance'])
                    self.activate_emergency_priority(closest['id'], closest['direction'])
            
            # Print status every 30 steps (3 seconds in simulation)
            if step % 30 == 0:
                current_phase = traci.trafficlight.getPhase(self.tl_id)
                phase_names = {0: "NS Green", 1: "NS Yellow", 2: "EW Green", 3: "EW Yellow"}
                status = "EMERGENCY" if self.emergency_active else "NORMAL"
                print(f"[{status}] Time: {traci.simulation.getTime():.1f}s | Phase: {phase_names.get(current_phase, 'Unknown')} | Vehicles: {len(traci.vehicle.getIDList())}")
        
        print("\n" + "="*60)
        print("Simulation completed")
        print(f"Total emergency vehicles processed: {len(self.processed_emergency_vehicles)}")
        print("="*60 + "\n")


def run_simulation(gui=True):
    """Initialize and run the SUMO simulation"""
    
    # SUMO configuration file
    sumo_cfg = "simulation.sumocfg"
    
    # Check if configuration file exists
    if not os.path.exists(sumo_cfg):
        print(f"Error: Configuration file '{sumo_cfg}' not found!")
        print("Please ensure all required files are in the current directory.")
        return
    
    # SUMO binary (with or without GUI)
    if gui:
        sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui.exe' if os.name == 'nt' else 'sumo-gui')
    else:
        sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo.exe' if os.name == 'nt' else 'sumo')
    
    # SUMO command
    sumo_cmd = [sumo_binary, "-c", sumo_cfg, "--start", "--quit-on-end"]
    
    # Start SUMO
    traci.start(sumo_cmd)
    
    try:
        # Create and run emergency vehicle priority system
        ev_priority = EmergencyVehiclePriority()
        ev_priority.run()
    finally:
        # Close SUMO
        traci.close()


if __name__ == "__main__":
    # Check command line arguments
    use_gui = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--no-gui":
            use_gui = False
        elif sys.argv[1] == "--gui":
            use_gui = True
        else:
            print("Usage: python emergency_vehicle_simulation.py [--gui|--no-gui]")
            sys.exit(1)
    
    run_simulation(gui=use_gui)
