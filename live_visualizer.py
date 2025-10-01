import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import os

class LiveVisualizer:
    """
    This class manages the real-time plotting of the V2V communication graph.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.pos = None  # Store node positions for a stable layout
        self.frame_count = 0
        # Create directory for live frames
        if not os.path.exists('live_frames'):
            os.makedirs('live_frames')

    def update_and_draw(self, events):
        """
        Updates the graph with new events from the simulation step and saves as image.
        """
        if not events:  # No events to process
            return
            
        graph_changed = False
        for event in events:
            if event['action'] == 'started':
                if not self.graph.has_node(event['source_id']):
                    self.graph.add_node(event['source_id'], type='starter', alert=event['alert_type'])
                    graph_changed = True
            elif event['action'] == 'received':
                # Ensure both nodes exist before adding an edge
                for node in [event['source_id'], event['receiver_id']]:
                    if not self.graph.has_node(node):
                        self.graph.add_node(node)
                        graph_changed = True
                self.graph.add_edge(event['source_id'], event['receiver_id'], label=f"{event['distance']:.1f}m")
            elif event['action'] == 'forwarded':
                if self.graph.has_node(event['source_id']):
                    self.graph.nodes[event['source_id']]['forwarded'] = True

        # Only redraw if there were changes
        if graph_changed or self.pos is None:
            self.pos = nx.spring_layout(self.graph, pos=self.pos, k=0.8, iterations=50)
            
            # Create new figure for this frame
            fig, ax = plt.subplots(figsize=(12, 10))

            # Determine node colors based on their state
            node_colors = []
            for node in self.graph.nodes(data=True):
                if node[1].get('type') == 'starter':
                    node_colors.append('red')
                elif node[1].get('forwarded'):
                    node_colors.append('orange')
                else:
                    node_colors.append('lightblue')

            # Draw the network graph
            nx.draw(self.graph, pos=self.pos, ax=ax, with_labels=True, node_size=2500, node_color=node_colors, font_size=10, font_weight='bold')
            edge_labels = nx.get_edge_attributes(self.graph, 'label')
            nx.draw_networkx_edge_labels(self.graph, pos=self.pos, ax=ax, edge_labels=edge_labels)

            ax.set_title(f"Live V2V Alert Propagation - Frame {self.frame_count}")
            
            # Save the frame
            plt.savefig(f'live_frames/frame_{self.frame_count:04d}.png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            self.frame_count += 1
            print(f"Saved frame {self.frame_count} to live_frames/frame_{self.frame_count-1:04d}.png")
