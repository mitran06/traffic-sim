import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import os

class Visualization:
    def __init__(self, log_file):
        self.log_file = log_file
        self.graph = nx.DiGraph()

    def create_graph_from_log(self):
        df = pd.read_csv(self.log_file)
        for index, row in df.iterrows():
            if row['action'] == 'started':
                self.graph.add_node(row['source_id'], type='starter', alert=row['alert_type'])
            elif row['action'] == 'received':
                self.graph.add_edge(row['source_id'], row['receiver_id'], label=f"{row['distance']:.1f}m")
            elif row['action'] == 'forwarded':
                if row['source_id'] in self.graph:
                    self.graph.nodes[row['source_id']]['forwarded'] = True

    def draw_graph(self):
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        node_colors = []
        for node in self.graph.nodes(data=True):
            if node[1].get('type') == 'starter':
                node_colors.append('red')
            elif node[1].get('forwarded'):
                node_colors.append('orange')
            else:
                node_colors.append('lightblue')

        nx.draw(self.graph, pos, with_labels=True, node_size=2000, node_color=node_colors, font_size=10, font_weight='bold')
        edge_labels = nx.get_edge_attributes(self.graph, 'label')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        
        plt.title("V2V Alert Propagation")
        plt.savefig("v2v_propagation.png")
        plt.close()

if __name__ == '__main__':
    log_file = "v2v_log_20250805_125923.csv" # replace with log file
    if os.path.exists(log_file):
        viz = Visualization(log_file)
        viz.create_graph_from_log()
        viz.draw_graph()
    else:
        print(f"Log file not found: {log_file}")
