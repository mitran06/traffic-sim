import os
from datetime import datetime
from v2v_communication import V2VCommunication
from simulation import SumoSimulation

if __name__ == "__main__":
    log_file = f"v2v_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(log_file, 'w') as f:
        f.write("time,source_id,receiver_id,alert_type,distance,action\n")

    sumo_config_file = "sumo_config/road.sumocfg"
    v2v_communicator = V2VCommunication(log_file)
    simulation = SumoSimulation(sumo_config_file, v2v_communicator)
    simulation.run()
