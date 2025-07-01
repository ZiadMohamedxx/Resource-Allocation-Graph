import sys
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
import networkx as nx
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QGridLayout, 
                             QWidget, QMessageBox, QInputDialog, QLabel)
from graph_manager import GraphManager

BUTTON_STYLE = """
    QPushButton {
        background-color: #a677d9;
        color: white;
        font-size: 16px;
        border-radius: 5px;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #472b66;
    }
    QPushButton:pressed {
        background-color: #3a294d;
    }
"""

class ResourceAllocationSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resource Allocation Graph")
        self.setGeometry(100, 100, 800, 500)
        self.graph_manager = GraphManager()
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        layout = QGridLayout()

        title = QLabel("Resource Allocation Graph Simulator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center; color: white;")

        subtitle = QLabel("Made By: Ziad Mohamed(247425) || Mohamed Hesham(244327) || Nada Emad(246215) || Mariam Salem(247179) || Omar Mostafa(249101)")
        subtitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #6699CC;")
    
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(subtitle, 1, 0, 1, 3)

        
        buttons = [
            ("Add Process", self.add_process),
            ("Add Resource", self.add_resource),
            ("Allocate/Request", self.manage_allocation),
            ("Release Allocation", self.release_resource),
            ("Remove Resource", self.remove_resource),
            ("Remove Process", self.remove_process),
            ("Check Deadlock", self.detect_deadlock)
        ]

        row, col = 2, 0
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setMinimumHeight(80)
            layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        #layout.addWidget(title, 0, 0, 1, 3)
        #layout.addWidget(subtitle, 1, 0, 1, 3)
        for i in range(row):
            layout.setRowStretch(i, 2)
        layout.setRowStretch(row, 0)
        for i in range(3):
            layout.setColumnStretch(i, 1)

        central_widget.setStyleSheet("background-color: #2E2E2E;")
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def add_process(self):
        process_id = self.graph_manager.add_process()
        QMessageBox.information(self, "Process Added", f"Added {process_id}")
        self.show_graph()

    def add_resource(self):
        quantity, ok = QInputDialog.getInt(self, "Resource Instances", "Enter number of instances:", 1, 1, 10, 1)
        if ok:
            resource_id = self.graph_manager.add_resource(quantity)
            QMessageBox.information(self, "Resource Added", f"Added {resource_id} with {quantity} instances")
        self.show_graph()

    def manage_allocation(self):
        processes = [n for n in self.graph_manager.graph.nodes if n.startswith("P")]
        resources = [n for n in self.graph_manager.graph.nodes if n.startswith("R")]
        if not processes or not resources:
            QMessageBox.warning(self, "Error", "Create at least one process and one resource")
            return
    
        process, ok = QInputDialog.getItem(self, "Select Process", "Process:", processes, 0, False)
        if not ok: return
        resource, ok = QInputDialog.getItem(self, "Select Resource", "Resource:", resources, 0, False)
        if not ok: return

        status = self.graph_manager.allocate_resource(process, resource)
        if status == "not enough instances":
            QMessageBox.information(self, "Request", f"{process} waiting for {resource}")
        else:
            QMessageBox.information(self, "Allocation", f"{resource} {status} to {process}")
        self.show_graph()

    def release_resource(self):
        allocations = [(u, v) for u, v in self.graph_manager.graph.edges if u.startswith("R") and v.startswith("P")]
        if not allocations:
            QMessageBox.warning(self, "Error", "No resources allocated")
            return

        allocation_strs = [f"{u} → {v}" for u, v in allocations]
        selection, ok = QInputDialog.getItem(self, "Release Resource", "Select allocation:", allocation_strs, 0, False)
        if not ok:
            return

        resource, process = selection.split(" → ")
        success = self.graph_manager.release_resource(resource, process)
        if success:
            QMessageBox.information(self, "Released", f"Released {resource} from {process}")
            # Check if a waiting process got the resource
            waiting_processes = [p for p in self.graph_manager.graph.predecessors(resource) 
                               if self.graph_manager.graph.has_edge(p, resource) and self.graph_manager.graph.edges[p, resource].get('style') == 'dashed']
            if not waiting_processes or self.graph_manager.resource_instances[resource]["available"] > 0:
                QMessageBox.information(self, "Resource Status", f"{resource} is now available")
        else:
            QMessageBox.warning(self, "Error", f"Failed to release {resource} from {process}")
        self.show_graph()

    def remove_resource(self):
        resources = [n for n in self.graph_manager.graph.nodes if n.startswith("R")]
        if not resources:
            QMessageBox.warning(self, "Error", "No resources available to remove")
            return

        resource, ok = QInputDialog.getItem(self, "Remove Resource", "Select Resource:", resources, 0, False)
        if not ok:
            return

        success = self.graph_manager.remove_resource(resource)
        if success:
            QMessageBox.information(self, "Resource Removed", f"{resource} has been removed")
            self.show_graph()

    def remove_process(self):
        processes = [n for n in self.graph_manager.graph.nodes if n.startswith("P")]
        if not processes:
            QMessageBox.warning(self, "Error", "No processes available to remove")
            return

        process, ok = QInputDialog.getItem(self, "Remove Process", "Select Process:", processes, 0, False)
        if not ok:
            return

        success = self.graph_manager.remove_process(process)
        if success:
            QMessageBox.information(self, "Process Removed", f"{process} has been removed")
            self.show_graph()
        else:
            QMessageBox.warning(self, "Error", f"Failed to remove {process}")

    def detect_deadlock(self):
        wfg = nx.DiGraph()
        processes = [n for n in self.graph_manager.graph.nodes if n.startswith("P")]
        wfg.add_nodes_from(processes)

        for process in processes:
            for resource in self.graph_manager.requests.get(process, {}):
                holders = [p for p in self.graph_manager.graph.successors(resource) 
                          if p.startswith("P") and self.graph_manager.allocations[p].get(resource, 0) > 0]
                for holder in holders:
                    if holder != process:
                        wfg.add_edge(process, holder)

        try:
            cycles = list(nx.simple_cycles(wfg))
            if cycles:
                deadlocked_processes = set()
                for cycle in cycles:
                    deadlocked_processes.update(cycle)
                QMessageBox.critical(self, "Deadlock Detected!", 
                                   f"Deadlock cycles found: {cycles}\nDeadlocked processes: {list(deadlocked_processes)}")
            else:
                QMessageBox.information(self, "No Deadlock", "System is safe")
        except nx.NetworkXNoCycle:
            QMessageBox.information(self, "No Deadlock", "System is safe")

    def show_graph(self):
        plt.clf()
        color_map = []
        labels = {}
        node_shapes = {}

        resource_instances = self.graph_manager.resource_instances

        for node in self.graph_manager.graph.nodes:
            if node.startswith("R"):
                labels[node] = f"{node} ({resource_instances.get(node, {'total': 0})['available']}/{resource_instances.get(node, {'total': 0})['total']})"
                color_map.append("#9370DB")
                node_shapes[node] = "s"
            else:
                labels[node] = node
                color_map.append("#44b0f2")
                node_shapes[node] = "o"

        pos = nx.spring_layout(self.graph_manager.graph)

        for shape in set(node_shapes.values()):
            nx.draw_networkx_nodes(self.graph_manager.graph, pos, 
                                   nodelist=[n for n in self.graph_manager.graph.nodes if node_shapes[n] == shape],
                                   node_shape=shape, 
                                   node_color=[color_map[i] for i, n in enumerate(self.graph_manager.graph.nodes) if node_shapes[n] == shape],
                                   node_size=2000)

        nx.draw_networkx_edges(self.graph_manager.graph, pos, 
                               edgelist=[(u, v) for u, v in self.graph_manager.graph.edges if self.graph_manager.graph.edges[u, v].get('style') != 'dashed'],
                               edge_color="gray", arrowsize=20)
        nx.draw_networkx_edges(self.graph_manager.graph, pos, 
                               edgelist=[(u, v) for u, v in self.graph_manager.graph.edges if self.graph_manager.graph.edges[u, v].get('style') == 'dashed'],
                               edge_color="orange", style='dashed', arrowsize=20)

        nx.draw_networkx_labels(self.graph_manager.graph, pos, labels, font_size=10)

        legend_labels = {
            "Process": plt.Line2D([0], [0], marker='o', color='w', markersize=10, markerfacecolor="#44b0f2"),
            "Resource": plt.Line2D([0], [0], marker='s', color='w', markersize=10, markerfacecolor="#9370DB"),
            "Allocation Edge": plt.Line2D([0], [0], color="gray", lw=2),
            "Request Edge": plt.Line2D([0], [0], color="orange", lw=2, linestyle="dashed")
        }

        plt.legend(handles=legend_labels.values(), labels=legend_labels.keys(), loc="upper right")
        plt.pause(0.1)
        plt.draw()
        plt.show()
