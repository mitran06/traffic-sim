import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import os
import numpy as np

class EmergencyClusterVisualizer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.graph = nx.Graph()
        
    def create_cluster_visualization(self):
        if not os.path.exists(self.log_file):
            print(f"Log file not found: {self.log_file}")
            return
            
        df = pd.read_csv(self.log_file)
        
        # Create multiple visualizations
        self.create_timeline_plot(df)
        self.create_cluster_network_graph(df)
        self.create_leadership_changes_plot(df)
        
    def create_timeline_plot(self, df):
        plt.figure(figsize=(15, 8))
        
        # Plot different event types over time
        event_types = df['event_type'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(event_types)))
        
        for i, event_type in enumerate(event_types):
            event_data = df[df['event_type'] == event_type]
            plt.scatter(event_data['time'], [i] * len(event_data), 
                       c=[colors[i]], label=event_type, s=60, alpha=0.7)
        
        plt.xlabel('Simulation Time (seconds)')
        plt.ylabel('Event Types')
        plt.title('Emergency Cluster System - Event Timeline')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('emergency_timeline.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("Timeline visualization saved as 'emergency_timeline.png'")
        
    def create_cluster_network_graph(self, df):
        plt.figure(figsize=(14, 10))
        
        # Build network graph from cluster relationships
        G = nx.Graph()
        
        # Add nodes and edges based on cluster relationships
        leader_events = df[df['event_type'] == 'leader_elected']
        emergency_spawns = df[df['event_type'] == 'emergency_spawn']
        
        # Add emergency vehicles as central nodes
        for _, row in emergency_spawns.iterrows():
            G.add_node(row['vehicle_id'], node_type='emergency', size=1000)
        
        # Add leaders and their relationships
        for _, row in leader_events.iterrows():
            cluster_id = row['cluster_id']
            leader_id = row['vehicle_id']
            
            # Extract emergency vehicle from cluster_id
            emergency_id = cluster_id.replace('cluster_', '')
            
            if emergency_id in G.nodes():
                G.add_node(leader_id, node_type='leader', size=500)
                G.add_edge(emergency_id, leader_id, weight=1/max(row['distance'], 1))
        
        if len(G.nodes()) > 0:
            # Create layout
            pos = nx.spring_layout(G, k=3, iterations=50)
            
            # Draw different node types with different colors
            emergency_nodes = [node for node, data in G.nodes(data=True) 
                             if data.get('node_type') == 'emergency']
            leader_nodes = [node for node, data in G.nodes(data=True) 
                          if data.get('node_type') == 'leader']
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, nodelist=emergency_nodes, 
                                 node_color='red', node_size=1000, 
                                 label='Emergency Vehicles', alpha=0.8)
            nx.draw_networkx_nodes(G, pos, nodelist=leader_nodes, 
                                 node_color='orange', node_size=500, 
                                 label='Cluster Leaders', alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, alpha=0.6, width=2)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            plt.title('Emergency Vehicle Cluster Network')
            plt.legend()
        else:
            plt.text(0.5, 0.5, 'No cluster relationships found in data', 
                    ha='center', va='center', transform=plt.gca().transAxes,
                    fontsize=14)
            plt.title('Emergency Vehicle Cluster Network - No Data')
            
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('emergency_cluster_network.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("Cluster network visualization saved as 'emergency_cluster_network.png'")
        
    def create_leadership_changes_plot(self, df):
        plt.figure(figsize=(12, 6))
        
        # Track leadership changes over time
        leader_events = df[df['event_type'].isin(['leader_elected', 'leader_changed', 'leader_lost'])]
        
        if len(leader_events) > 0:
            # Group by cluster and plot leadership timeline
            clusters = leader_events['cluster_id'].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(clusters)))
            
            for i, cluster in enumerate(clusters):
                cluster_events = leader_events[leader_events['cluster_id'] == cluster]
                
                times = cluster_events['time'].values
                leaders = cluster_events['vehicle_id'].values
                event_types = cluster_events['event_type'].values
                
                # Plot leadership changes
                for j, (time, leader, event_type) in enumerate(zip(times, leaders, event_types)):
                    marker = 'o' if event_type == 'leader_elected' else '^' if event_type == 'leader_changed' else 'x'
                    plt.scatter(time, i, c=[colors[i]], marker=marker, s=100, alpha=0.8)
                    
                    # Add leader ID as text
                    plt.annotate(leader, (time, i), xytext=(5, 5), 
                               textcoords='offset points', fontsize=8)
            
            plt.xlabel('Simulation Time (seconds)')
            plt.ylabel('Cluster Index')
            plt.title('Leadership Changes Over Time')
            plt.grid(True, alpha=0.3)
            
            # Create custom legend
            plt.scatter([], [], marker='o', c='gray', s=100, label='Leader Elected')
            plt.scatter([], [], marker='^', c='gray', s=100, label='Leader Changed')
            plt.scatter([], [], marker='x', c='gray', s=100, label='Leader Lost')
            plt.legend()
        else:
            plt.text(0.5, 0.5, 'No leadership events found in data', 
                    ha='center', va='center', transform=plt.gca().transAxes,
                    fontsize=14)
            plt.title('Leadership Changes Over Time - No Data')
        
        plt.tight_layout()
        plt.savefig('emergency_leadership_changes.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("Leadership changes visualization saved as 'emergency_leadership_changes.png'")

if __name__ == '__main__':
    # Find the most recent log file
    log_files = [f for f in os.listdir('.') if f.startswith('emergency_cluster_log_') and f.endswith('.csv')]
    
    if log_files:
        # Use the most recent log file
        log_file = sorted(log_files)[-1]
        print(f"Using log file: {log_file}")
        
        viz = EmergencyClusterVisualizer(log_file)
        viz.create_cluster_visualization()
        
        print("\nVisualization complete! Generated files:")
        print("- emergency_timeline.png")
        print("- emergency_cluster_network.png") 
        print("- emergency_leadership_changes.png")
    else:
        print("No emergency cluster log files found. Run 'python emergency_main.py' first.")
