import os
import sys
from datetime import datetime
import random
from emergency_cluster_system import EmergencyClusterSystem

class EmergencySimulation:
    def __init__(self, sumo_cfg_path, cluster_system):
        self.sumo_cfg_path = sumo_cfg_path
        self.cluster_system = cluster_system
        self.traci = None
        self.simulation_time = 0

    def _get_traci(self):
        if self.traci is None:
            if 'SUMO_HOME' in os.environ:
                tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
                sys.path.append(tools)
                import traci
                self.traci = traci
            else:
                sys.exit("please declare environment variable 'SUMO_HOME'")
        return self.traci

    def run(self):
        traci = self._get_traci()
        sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui')
        sumo_cmd = [sumo_binary, "-c", self.sumo_cfg_path]

        traci.start(sumo_cmd)
        
        # Track when emergency vehicles are added
        emergency_vehicles_added = set()
        
        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            self.simulation_time = traci.simulation.getTime()
            
            # Detect and add emergency vehicles
            current_vehicles = traci.vehicle.getIDList()
            for veh_id in current_vehicles:
                if "ambulance" in veh_id and veh_id not in emergency_vehicles_added:
                    self.cluster_system.add_emergency_vehicle(veh_id, priority_level=1)
                    emergency_vehicles_added.add(veh_id)
                    print(f"Emergency vehicle {veh_id} detected and added to system")
            
            # Update cluster system
            events = self.cluster_system.update_all_positions()
            
            # Debug: Print vehicle counts
            if step % 20 == 0:  # Every 20 steps
                current_vehicles = traci.vehicle.getIDList()
                regular_vehicles = [v for v in current_vehicles if "ambulance" not in v]
                emergency_vehicles = [v for v in current_vehicles if "ambulance" in v]
                print(f"DEBUG Step {step}: {len(regular_vehicles)} regular vehicles, {len(emergency_vehicles)} emergency vehicles")
            
            # Print cluster status every 10 steps for monitoring
            if step % 10 == 0 and step > 0:
                self.print_cluster_status()
            
            step += 1
        
        traci.close()
        
    def print_cluster_status(self):
        clusters = self.cluster_system.get_cluster_info()
        emergency_vehicles = self.cluster_system.get_emergency_vehicles()
        
        print(f"\n=== Cluster Status at Time {self.simulation_time:.1f} ===")
        for cluster_id, cluster_info in clusters.items():
            print(f"Cluster {cluster_id}:")
            print(f"  Emergency Vehicle: {cluster_info['emergency_vehicle']}")
            print(f"  Leader: {cluster_info['leader']}")
            print(f"  Members: {cluster_info['size']} vehicles")
            print(f"  Member IDs: {cluster_info['members'][:5]}...")  # Show first 5
        print("=" * 50)

if __name__ == "__main__":
    log_file = f"emergency_cluster_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(log_file, 'w') as f:
        f.write("time,event_type,vehicle_id,cluster_id,distance\n")

    sumo_config_file = "sumo_config/road.sumocfg"
    cluster_system = EmergencyClusterSystem(log_file)
    simulation = EmergencySimulation(sumo_config_file, cluster_system)
    simulation.run()
    
    print(f"\nSimulation completed! Log saved to: {log_file}")
    print("Run 'python emergency_visualizer.py' to generate cluster visualization.")
