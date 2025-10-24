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
        self.normal_phase_duration = 20  # Normal green phase duration
        self.emergency_phase_duration = 25  # Emergency green phase duration
        self.yellow_duration = 3  # Yellow phase duration
        
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
        print(f"[PRIORITY] Activating emergency priority for {vehicle_id}")
        print(f"[PRIORITY] Direction: {direction}")
        print(f"[PRIORITY] Duration: {self.emergency_phase_duration} seconds")
        print(f"{'='*60}\n")
        
        self.emergency_active = True
        self.emergency_vehicle_id = vehicle_id
        self.emergency_direction = direction
        self.emergency_start_time = traci.simulation.getTime()
        
        # Set traffic light to green for emergency vehicle direction
        if direction == 'NS':
            # Set North-South to green
            current_phase = traci.trafficlight.getPhase(self.tl_id)
            
            # If currently in EW phase, switch to yellow first
            if current_phase in [self.PHASE_EW_GREEN]:
                traci.trafficlight.setPhase(self.tl_id, self.PHASE_EW_YELLOW)
                traci.trafficlight.setPhaseDuration(self.tl_id, self.yellow_duration)
            else:
                # Switch directly to NS green with extended duration
                traci.trafficlight.setPhase(self.tl_id, self.PHASE_NS_GREEN)
                traci.trafficlight.setPhaseDuration(self.tl_id, self.emergency_phase_duration)
                
        elif direction == 'EW':
            # Set East-West to green
            current_phase = traci.trafficlight.getPhase(self.tl_id)
            
            # If currently in NS phase, switch to yellow first
            if current_phase in [self.PHASE_NS_GREEN]:
                traci.trafficlight.setPhase(self.tl_id, self.PHASE_NS_YELLOW)
                traci.trafficlight.setPhaseDuration(self.tl_id, self.yellow_duration)
            else:
                # Switch directly to EW green with extended duration
                traci.trafficlight.setPhase(self.tl_id, self.PHASE_EW_GREEN)
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
            
            # If vehicle is on outgoing edge, it has passed
            if '_out' in road_id or road_id == '':
                print(f"[INFO] Emergency vehicle {self.emergency_vehicle_id} has passed the intersection")
                return True
            
            # Check if minimum emergency duration has elapsed
            current_time = traci.simulation.getTime()
            elapsed_time = current_time - self.emergency_start_time
            
            if elapsed_time >= self.emergency_phase_duration:
                print(f"[INFO] Emergency priority duration completed ({elapsed_time:.1f}s)")
                return True
                
        except:
            return True
        
        return False
    
    def deactivate_emergency_priority(self):
        """Deactivate emergency priority and return to normal operation"""
        print(f"\n{'='*60}")
        print(f"[NORMAL] Returning to normal traffic light operation")
        print(f"[NORMAL] Emergency vehicle {self.emergency_vehicle_id} has been processed")
        print(f"{'='*60}\n")
        
        # Mark vehicle as processed
        self.processed_emergency_vehicles.add(self.emergency_vehicle_id)
        
        # Reset state
        self.emergency_active = False
        self.emergency_vehicle_id = None
        self.emergency_direction = None
        self.emergency_start_time = 0
        
        # Resume normal traffic light program
        # Let it continue with current phase but restore normal durations
        current_phase = traci.trafficlight.getPhase(self.tl_id)
        
        if current_phase in [self.PHASE_NS_GREEN, self.PHASE_EW_GREEN]:
            traci.trafficlight.setPhaseDuration(self.tl_id, self.normal_phase_duration)
        else:
            traci.trafficlight.setPhaseDuration(self.tl_id, self.yellow_duration)
    
    def run(self):
        """Main simulation loop"""
        print("\n" + "="*60)
        print("SUMO Emergency Vehicle Priority System")
        print("="*60)
        print(f"Normal green phase: {self.normal_phase_duration}s")
        print(f"Emergency green phase: {self.emergency_phase_duration}s")
        print(f"Yellow phase: {self.yellow_duration}s")
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
