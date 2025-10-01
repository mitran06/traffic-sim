import traci
import math
import uuid
from datetime import datetime

class EmergencyVehicle:
    def __init__(self, vehicle_id, priority_level=1):
        self.vehicle_id = vehicle_id
        self.priority_level = priority_level
        self.position = (0, 0)
        self.speed = 0
        self.cluster_radius = 75  # Reduced from 100 to 75 meters for better clustering
        
    def update_position(self):
        if self.vehicle_id in traci.vehicle.getIDList():
            self.position = traci.vehicle.getPosition(self.vehicle_id)
            self.speed = traci.vehicle.getSpeed(self.vehicle_id)
            return True
        return False

class ClusterVehicle:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.position = (0, 0)
        self.speed = 0
        self.is_leader = False
        self.cluster_id = None
        self.distance_to_emergency = float('inf')
        self.leadership_score = 0
        
    def update_position(self):
        if self.vehicle_id in traci.vehicle.getIDList():
            self.position = traci.vehicle.getPosition(self.vehicle_id)
            self.speed = traci.vehicle.getSpeed(self.vehicle_id)
            return True
        return False
    
    def calculate_leadership_score(self, emergency_vehicle):
        # Leadership score based on distance to emergency vehicle and stability
        distance = math.sqrt((self.position[0] - emergency_vehicle.position[0])**2 + 
                           (self.position[1] - emergency_vehicle.position[1])**2)
        
        # Closer vehicles and vehicles with moderate speed have higher scores
        distance_score = max(0, 100 - distance)  # Closer = higher score
        speed_stability = max(0, 30 - abs(self.speed - 15))  # Prefer moderate speeds
        
        self.leadership_score = distance_score + speed_stability
        self.distance_to_emergency = distance
        return self.leadership_score

class EmergencyClusterSystem:
    def __init__(self, log_file):
        self.emergency_vehicles = {}
        self.cluster_vehicles = {}
        self.clusters = {}
        self.log_file = log_file
        self.cluster_events = []
        
    def add_emergency_vehicle(self, vehicle_id, priority_level=1):
        self.emergency_vehicles[vehicle_id] = EmergencyVehicle(vehicle_id, priority_level)
        self.log_cluster_event("emergency_spawn", vehicle_id, "", 0)
        
    def update_all_positions(self):
        events = []
        
        # Update emergency vehicles
        for emerg_id, emerg_vehicle in list(self.emergency_vehicles.items()):
            if not emerg_vehicle.update_position():
                del self.emergency_vehicles[emerg_id]
                continue
                
        # Update cluster vehicles
        current_vehicles = traci.vehicle.getIDList()
        
        # Remove vehicles that left the simulation
        for veh_id in list(self.cluster_vehicles.keys()):
            if veh_id not in current_vehicles:
                del self.cluster_vehicles[veh_id]
                
        # Add/update current vehicles
        for veh_id in current_vehicles:
            if veh_id not in self.emergency_vehicles:  # Don't cluster emergency vehicles
                if veh_id not in self.cluster_vehicles:
                    self.cluster_vehicles[veh_id] = ClusterVehicle(veh_id)
                self.cluster_vehicles[veh_id].update_position()
        
        # Update clusters for each emergency vehicle
        for emerg_id, emerg_vehicle in self.emergency_vehicles.items():
            cluster_events = self.update_cluster(emerg_vehicle)
            events.extend(cluster_events)
            
        return events
    
    def update_cluster(self, emergency_vehicle):
        events = []
        cluster_id = f"cluster_{emergency_vehicle.vehicle_id}"
        
        # Debug: Print emergency vehicle position
        print(f"DEBUG: Emergency vehicle {emergency_vehicle.vehicle_id} at position {emergency_vehicle.position}")
        
        # Find vehicles within cluster radius
        cluster_members = []
        nearby_vehicles = 0
        for veh_id, cluster_vehicle in self.cluster_vehicles.items():
            distance = math.sqrt((cluster_vehicle.position[0] - emergency_vehicle.position[0])**2 + 
                               (cluster_vehicle.position[1] - emergency_vehicle.position[1])**2)
            
            # Debug: Show all nearby vehicles
            if distance <= 150:  # Show vehicles within 150m for debugging
                nearby_vehicles += 1
                print(f"DEBUG: Vehicle {veh_id} at distance {distance:.1f}m from emergency vehicle")
            
            if distance <= emergency_vehicle.cluster_radius:
                cluster_vehicle.cluster_id = cluster_id
                cluster_vehicle.calculate_leadership_score(emergency_vehicle)
                cluster_members.append(cluster_vehicle)
                print(f"DEBUG: Vehicle {veh_id} JOINED cluster at distance {distance:.1f}m")
            else:
                # Vehicle left the cluster
                if cluster_vehicle.cluster_id == cluster_id:
                    if cluster_vehicle.is_leader:
                        events.append(self.log_cluster_event("leader_lost", veh_id, cluster_id, distance))
                    cluster_vehicle.cluster_id = None
                    cluster_vehicle.is_leader = False
        
        print(f"DEBUG: Found {nearby_vehicles} vehicles within 150m, {len(cluster_members)} in cluster")
        
        # Select new leader if we have cluster members
        if cluster_members:
            # Sort by leadership score (highest first)
            cluster_members.sort(key=lambda x: x.leadership_score, reverse=True)
            new_leader = cluster_members[0]
            
            # Check if leader changed
            current_leader = None
            for vehicle in cluster_members:
                if vehicle.is_leader:
                    current_leader = vehicle
                    break
            
            if current_leader != new_leader:
                # Remove old leader status
                if current_leader:
                    current_leader.is_leader = False
                    events.append(self.log_cluster_event("leader_changed", current_leader.vehicle_id, cluster_id, current_leader.distance_to_emergency))
                
                # Assign new leader
                new_leader.is_leader = True
                events.append(self.log_cluster_event("leader_elected", new_leader.vehicle_id, cluster_id, new_leader.distance_to_emergency))
            
            # Update cluster information
            self.clusters[cluster_id] = {
                'emergency_vehicle': emergency_vehicle.vehicle_id,
                'leader': new_leader.vehicle_id,
                'members': [v.vehicle_id for v in cluster_members],
                'size': len(cluster_members)
            }
        else:
            # No cluster members, remove cluster if it exists
            if cluster_id in self.clusters:
                del self.clusters[cluster_id]
            
        return events
    
    def log_cluster_event(self, event_type, vehicle_id, cluster_id, distance):
        timestamp = traci.simulation.getTime() if 'traci' in globals() else 0
        event = {
            'time': timestamp,
            'event_type': event_type,
            'vehicle_id': vehicle_id,
            'cluster_id': cluster_id,
            'distance': distance
        }
        
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp},{event_type},{vehicle_id},{cluster_id},{distance}\n")
            
        print(f"Time: {timestamp:.1f}, {event_type}: Vehicle {vehicle_id} in {cluster_id} (dist: {distance:.1f}m)")
        return event
    
    def get_cluster_info(self):
        return self.clusters
    
    def get_emergency_vehicles(self):
        return self.emergency_vehicles
    
    def get_cluster_vehicles(self):
        return self.cluster_vehicles
