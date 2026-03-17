from Devices.Valvebox.valvebox_python_api import valves
from Devices.HotPlate.hotplate_api import HotPlate
from Devices.SyringePump.syringe_pump_api import syring_pump
from Devices.device_commands import create_command_dict
from Devices.NMR.nmr_api import NMR
import json
"""NOTES:
    components.json :
        Remove Name tag"""
class valve_node_tree:
    

    def __init__(self, components):
        print(components)
        self.nodes = json.load(open("./Devices/DeviceTransport/node_tree.json"))
        self._update_nodes(components)

    def _update_nodes(self, components):
        """Read component dictionary and tie components to respective nodes. save."""
        """Child node is ALWAYS on port 8, parent ALWAYS on 1 parent connects to main"""
        """output nodes: parent node connects to main (pushes stuff to components)
            input node: parent node connects to 1 (acts as an intake valve)"""
        self.distribute_nodes = []
        self.gather_nodes = []
        for component in components["components"]:
            print(component)
            for valve_connection in components["components"][component]["valve_connections"]:
                valve = valve_connection[0]
                port = valve_connection[1]-1
                self.nodes[str(valve)]["connections"][port] = components["components"][component]["name"]
                #TODO insert save method here

        for node in self.nodes:
            if self.nodes[node]["type"] == "distribute":
                self.distribute_nodes.append(node)
            elif self.nodes[node]["type"] == "gather":
                self.gather_nodes.append(node)
    def _find_nodes_with(self, item):
        """Return list of nodes with item in connections"""
        apperance_list = []
        for node in self.nodes:
            if item in self.nodes[node]["connections"]:
                apperance_list.append(node)
        return(apperance_list)
    
    def _find_intake_nodes_with(self, item):
        return_list = []
        nodes = self._find_nodes_with(item)
        for node in nodes:
            if self.nodes[node]["type"] == "intake":
                return_list.append(node)
        return return_list

    def _find_output_nodes_with(self, item):
        return_list = []
        nodes = self._find_nodes_with(item)
        for node in nodes:
            if self.nodes[node]["type"] == "output":
                return_list.append(node)
        return return_list

    def _closest_node_path(self, start, finish):
        start_nodes = self._find_intake_nodes_with(start)
        print(start_nodes)
        finish_nodes = self._find_output_nodes_with(finish)
        closest_distance = 9999

        #TODO This is not optimized for Multiport connections
        for start_point in start_nodes:
            for end_point in finish_nodes:
                if (abs(int(start_point)-int(end_point))) < closest_distance and int(start_point) < int(end_point):
                    closest_distance = abs(int(start_point)-int(end_point))
                    closest_nodes = [start_point, end_point]
        if(closest_distance == 9999):
            return []
        else:
            return closest_nodes 
    

    def _find_path(self, start, finish):
        """Returns list of valve-port pairs to set a path between two components"""
        start_end = self._closest_node_path(start, finish)
        steps = int(start_end[1])-int(start_end[0])
        valve_path = []

        first_step = [start_end[0],self.nodes[start_end[0]]["connections"].index(start)+1]
        valve_path.append(first_step)

        last_step = [start_end[1],self.nodes[start_end[1]]["connections"].index(finish)+1]

        for node in range(int(start_end[0])+1,int(start_end[1])):
            if self.nodes[node]["type"] == "intake":
                step = [node, 1]
            elif self.nodes[node]["type"] == "output":
                step = [node, 8]
            valve_path.append(step)
        
        valve_path.append(last_step)

        return (valve_path)


    

