import os
import sys
from datetime import datetime
import random

class SumoSimulation:
    def __init__(self, sumo_cfg_path, v2v_communicator):
        self.sumo_cfg_path = sumo_cfg_path
        self.v2v_communicator = v2v_communicator
        self.traci = None

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
        
        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            self.v2v_communicator.update_vehicle_states()

            if random.random() < 0.01 and traci.vehicle.getIDCount() > 0:
                veh_id = random.choice(traci.vehicle.getIDList())
                event_type = random.choice(["road_hazard", "accident"])
                self.v2v_communicator.simulate_random_events(event_type, veh_id)
                
            step += 1
        
        traci.close()
