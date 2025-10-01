import traci
import math
import uuid

class V2VCommunication:
    def __init__(self, log_file):
        self.vehicles = {}
        self.log_file = log_file

    def get_distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def broadcast_alert(self, source_id, alert_type, alert_id, hop_count=0):
        if source_id not in self.vehicles:
            return

        source_pos = self.vehicles[source_id]['pos']
        
        for veh_id, veh_data in self.vehicles.items():
            if veh_id != source_id:
                if alert_id in veh_data.get('processed_alerts', set()):
                    continue

                distance = self.get_distance(source_pos, veh_data['pos'])
                if distance <= 50:
                    print(f"Time: {traci.simulation.getTime()}, Alert {alert_id[:4]} from {source_id} to {veh_id}")
                    self.log_event(traci.simulation.getTime(), source_id, veh_id, alert_type, distance, "received")
                    self.vehicles[veh_id].setdefault('processed_alerts', set()).add(alert_id)
                    self.evaluate_and_forward(veh_id, source_id, alert_type, alert_id, hop_count + 1)

    def evaluate_and_forward(self, receiver_id, original_source_id, alert_type, alert_id, hop_count):
        if hop_count > 5:
            print(f"Time: {traci.simulation.getTime()}, {receiver_id} stops forwarding {alert_id[:4]}, max hops.")
            self.log_event(traci.simulation.getTime(), receiver_id, "", alert_type, 0, "stopped_max_hops")
            return

        print(f"Time: {traci.simulation.getTime()}, {receiver_id} is forwarding alert {alert_id[:4]}.")
        self.log_event(traci.simulation.getTime(), receiver_id, "", alert_type, 0, "forwarded")
        self.broadcast_alert(receiver_id, alert_type, alert_id, hop_count)

    def update_vehicle_states(self):
        current_vehicles = traci.vehicle.getIDList()
        
        for veh_id in list(self.vehicles.keys()):
            if veh_id not in current_vehicles:
                del self.vehicles[veh_id]

        for veh_id in current_vehicles:
            pos = traci.vehicle.getPosition(veh_id)
            speed = traci.vehicle.getSpeed(veh_id)
            
            if veh_id in self.vehicles:
                prev_speed = self.vehicles[veh_id]['speed']
                if prev_speed - speed > 5:
                    alert_id = str(uuid.uuid4())
                    print(f"Time: {traci.simulation.getTime()}, Brake-check by {veh_id}, starting alert {alert_id[:4]}")
                    self.log_event(traci.simulation.getTime(), veh_id, "", "brake_check", 0, "started")
                    self.vehicles[veh_id].setdefault('processed_alerts', set()).add(alert_id)
                    self.broadcast_alert(veh_id, "brake_check", alert_id)
            
            if veh_id not in self.vehicles:
                self.vehicles[veh_id] = {'pos': pos, 'speed': speed, 'processed_alerts': set()}
            else:
                self.vehicles[veh_id]['pos'] = pos
                self.vehicles[veh_id]['speed'] = speed

    def simulate_random_events(self, event_type, veh_id):
        alert_id = str(uuid.uuid4())
        if veh_id in self.vehicles and alert_id not in self.vehicles[veh_id].get('processed_alerts', set()):
            print(f"Time: {traci.simulation.getTime()}, Event: {event_type} by {veh_id}, starting alert {alert_id[:4]}")
            self.log_event(traci.simulation.getTime(), veh_id, "", event_type, 0, "started")
            self.vehicles[veh_id].setdefault('processed_alerts', set()).add(alert_id)
            self.broadcast_alert(veh_id, event_type, alert_id)

    def log_event(self, time, source_id, receiver_id, alert_type, distance, action):
        with open(self.log_file, 'a') as f:
            f.write(f"{time},{source_id},{receiver_id},{alert_type},{distance},{action}\n")
