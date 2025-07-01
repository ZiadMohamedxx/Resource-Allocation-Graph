import networkx as nx

class GraphManager:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.process_count = 0
        self.resource_count = 0
        self.resource_instances = {}  # {resource: {"total": int, "available": int}}
        self.allocations = {}  # {process: {resource: allocated_count}}
        self.requests = {}    # {process: {resource: requested_count}}

    def add_process(self):
        process_id = f"P{self.process_count}"
        self.graph.add_node(process_id)
        self.allocations[process_id] = {}
        self.requests[process_id] = {}
        self.process_count += 1
        return process_id

    def add_resource(self, instances):
        resource_id = f"R{self.resource_count}"
        self.graph.add_node(resource_id)
        self.resource_instances[resource_id] = {"total": instances, "available": instances}
        self.resource_count += 1
        return resource_id

    def allocate_resource(self, process, resource):
        if resource not in self.resource_instances or process not in self.allocations:
            return "does not exist"

        if self.resource_instances[resource]["available"] > 0:
            self.resource_instances[resource]["available"] -= 1
            self.allocations[process][resource] = self.allocations[process].get(resource, 0) + 1
            self.graph.add_edge(resource, process)  # Allocation edge
            # Clear request if it exists
            if resource in self.requests[process]:
                del self.requests[process][resource]
                if self.graph.has_edge(process, resource):
                    self.graph.remove_edge(process, resource)
            return "allocated"
        
        # Add or increment request
        self.requests[process][resource] = self.requests[process].get(resource, 0) + 1
        self.graph.add_edge(process, resource, style='dashed', color='orange')
        return "not enough instances"

    def release_resource(self, resource, process):
        if resource in self.allocations.get(process, {}) and self.allocations[process][resource] > 0:
            self.resource_instances[resource]["available"] += 1
            self.allocations[process][resource] -= 1
            if self.allocations[process][resource] == 0:
                del self.allocations[process][resource]
                if self.graph.has_edge(resource, process):
                    self.graph.remove_edge(resource, process)

            # Check waiting processes and allocate if possible
            waiting_processes = [p for p in self.graph.predecessors(resource) 
                               if self.graph.has_edge(p, resource) and self.graph.edges[p, resource].get('style') == 'dashed']
            if waiting_processes and self.resource_instances[resource]["available"] > 0:
                next_process = waiting_processes[0]  # Pick first waiting process
                self.allocate_resource(next_process, resource)  # Attempt allocation
            return True
        return False

    def remove_resource(self, resource):
        if resource in self.resource_instances:
            del self.resource_instances[resource]
            self.graph.remove_node(resource)
            return True
        return False

    def remove_process(self, process):
        if process in self.allocations:
            for resource in list(self.allocations[process].keys()):
                self.release_resource(resource, process)
            del self.allocations[process]
            del self.requests[process]
        if process in self.graph.nodes:
            self.graph.remove_node(process)
            return True
        return False
