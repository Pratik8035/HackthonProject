import pandas as pd
import networkx as nx

class RouteOptimizer:
    def __init__(self, route_file='datasets/route_dataset.csv'):
        self.route_file = route_file
        self.graph = nx.Graph()
        self._build_graph()

    def _build_graph(self):
        try:
            df = pd.read_csv(self.route_file)
            for _, row in df.iterrows():
                src = row['source_port']
                dest = row['destination_port']
                dist = row['distance_km']
                days = row['expected_transit_days']
                
                # Add edge, if exists keep the shortest distance
                if self.graph.has_edge(src, dest):
                    if self.graph[src][dest]['weight'] > dist:
                        self.graph.add_edge(src, dest, weight=dist, days=days)
                else:
                    self.graph.add_edge(src, dest, weight=dist, days=days)
        except Exception as e:
            print(f"Error building graph: {e}")

    def get_ports(self):
        return list(self.graph.nodes())

    def find_best_route(self, source, target):
        if source not in self.graph or target not in self.graph:
            return None, None, None
            
        try:
            path = nx.dijkstra_path(self.graph, source, target, weight='weight')
            
            total_dist = 0
            total_days = 0
            
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i+1]
                total_dist += self.graph[u][v]['weight']
                total_days += self.graph[u][v]['days']
                
            return path, total_dist, total_days
        except nx.NetworkXNoPath:
            return None, None, None
