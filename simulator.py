import sys
import networkx as nx
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QWidget, QMessageBox, QInputDialog)

class ResourceAllocationSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resource Allocation Graph Simulator")
        self.setGeometry(100, 100, 800, 600)
        
        self.graph = nx.DiGraph()
        self.resource_instances = {}  # Track available resource instances
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        buttons = [
            ("Add Process", self.add_process),
            ("Add Resource", self.add_resource),
            ("Allocate/Request", self.manage_allocation),
            ("Release Resource", self.release_resource),
            ("Check Deadlock", self.detect_deadlock),
            ("Show Graph", self.show_graph)
        ]

        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def add_process(self):
        process_id = f"P{len([n for n in self.graph.nodes if n.startswith('P')]) + 1}"
        self.graph.add_node(process_id, color="blue")
        QMessageBox.information(self, "Process Added", f"Added {process_id}")

    def add_resource(self):
        resource_id = f"R{len([n for n in self.graph.nodes if n.startswith('R')]) + 1}"
        quantity, ok = QInputDialog.getInt(self, "Resource Instances", 
                                         "Enter number of instances:", 1, 1, 10, 1)
        if ok:
            self.resource_instances[resource_id] = quantity
            self.graph.add_node(resource_id, color="red")
            QMessageBox.information(self, "Resource Added", 
                                  f"Added {resource_id} with {quantity} instances")

    def manage_allocation(self):
        processes = [n for n in self.graph.nodes if n.startswith("P")]
        resources = [n for n in self.graph.nodes if n.startswith("R")]

        if not processes or not resources:
            QMessageBox.warning(self, "Error", "Create at least one process and resource")
            return

        process, ok = QInputDialog.getItem(self, "Select Process", "Process:", processes, 0, False)
        if not ok: return
        
        resource, ok = QInputDialog.getItem(self, "Select Resource", "Resource:", resources, 0, False)
        if not ok: return

        if self.resource_instances.get(resource, 0) > 0:
            # Allocate resource (resource -> process)
            self.graph.add_edge(resource, process)
            self.resource_instances[resource] -= 1
            QMessageBox.information(self, "Allocation", 
                                  f"Allocated {resource} to {process}")
        else:
            # Add request edge (process -> resource)
            self.graph.add_edge(process, resource)
            QMessageBox.information(self, "Request", 
                                  f"{process} waiting for {resource}")

    def release_resource(self):
        # Find allocated resources (resource -> process edges)
        allocations = [(u, v) for u, v in self.graph.edges 
                      if u.startswith("R") and v.startswith("P")]

        if not allocations:
            QMessageBox.warning(self, "Error", "No resources allocated")
            return

        resource, process = QInputDialog.getItem(self, "Release Resource", 
                                               "Select allocation:", 
                                               [f"{u} → {v}" for u, v in allocations], 0, False)
        if not resource: return

        u, v = resource.split(" → ")
        self.graph.remove_edge(u, v)
        self.resource_instances[u] += 1
        QMessageBox.information(self, "Released", f"Released {u} from {v}")

    def detect_deadlock(self):
        try:
            # Find if any process is both requesting and part of a cycle
            cycle = nx.find_cycle(self.graph, orientation="original")
            QMessageBox.critical(self, "Deadlock Detected!", f"Deadlock cycle: {cycle}")
        except nx.NetworkXNoCycle:
            if any(e for e in self.graph.edges if e[0].startswith("P")):
                QMessageBox.warning(self, "Warning", 
                                  "Potential deadlock (requests exist but no cycle)")
            else:
                QMessageBox.information(self, "No Deadlock", "System is safe")

    def show_graph(self):
        plt.clf()
        color_map = []
        labels = {}
        
        for node in self.graph.nodes:
            color_map.append("blue" if node.startswith("P") else "red")
            if node.startswith("R"):
                labels[node] = f"{node}\n({self.resource_instances[node]} available)"
            else:
                labels[node] = node

        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, labels=labels, 
               node_color=color_map, edge_color="gray",
               node_size=2000, font_size=10, arrowsize=20)
        plt.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResourceAllocationSimulator()
    window.show()
    sys.exit(app.exec())
