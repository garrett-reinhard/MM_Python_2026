from Devices.Valvebox.valvebox_python_api import valves
from Devices.HotPlate.hotplate_api import HotPlate
from Devices.SyringePump.syringe_pump_api import syring_pump
from Devices.NMR.nmr_api import NMR
import sys
import json
class NodeTree:
    

    def __init__(self, components):
        self.nodes = json.load(open("./Devices/DeviceTransport/node_tree.json"))
        self.acceptable_hotplate_range = 10 #variance in hotplate setpoints that is acceptable

        self._update_nodes(components)

    def _update_nodes(self, components):
        """Read component dictionary and tie components to respective nodes. save."""
        """Child node is ALWAYS on port 8, parent ALWAYS on 1 parent connects to main"""
        """output nodes: parent node connects to main (pushes stuff to components)
            input node: parent node connects to 1 (acts as an intake valve)"""
        
        """Developer notes: This is a section I want to come back to. The components vs. node_tree json files is confusing
            components is easier for the end user to read.  I think node_tree.json shouldn't really ever be edited by the users.
            The only info that the program really gets from node_tree is whether the node is odd/ever (in/out).  Optimally,
            this should be swapped for a system where it just searches for 2 nodes that are odd numbers of spaces away.
            The parent/child stuff is never used though, and is simply assumed (see note above)

            note; name in components.json is redundant
            TLDR: components vs nodes is confusing"""
        
        #NOTE: nothing should be connected to port 1 of any valve.

        self.components = components
        for component in components:

            for valve_connection in components[component]["valve_connections"]:
                valve = valve_connection[0]
                port = valve_connection[1]-1 #-1 so that ports are used 1-8 and not 0-7
                #print(self.nodes[str(valve)]["connections"])
                #print(port, valve)
                self.nodes[str(valve)]["connections"][port] = component
                #TODO insert save method here

            #Prior to removing connections 
            """
            #Add syringe_pump connection list
            if(components[component]["type"] != "syringe_pump"):
                for connection in components[component]["connections"]:
                    location = connection[0]
                    port = int(connection[1]-1)
                    self.components[location]["connections"][port] = component
            """

    def _find_nodes_with(self, item):
        """Return list of nodes with item in connections"""
        apperance_list = []
        for node in self.nodes:
            if item in self.nodes[node]["connections"]:
                apperance_list.append(node)
        return(apperance_list)
    
    def _find_intake_nodes_with(self, item):
        print("Find_intake")
        #print(self.nodes)
        return_list = []
        nodes = self._find_nodes_with(item)
        for node in nodes:
            if int(node) % 2 == 1:
                return_list.append(node)
        print(return_list)
        return return_list

    def _find_output_nodes_with(self, item):
        print("Finding Outputs")
        return_list = []
        nodes = self._find_nodes_with(item)
        for node in nodes:
            if int(node) % 2 == 0:
                return_list.append(node)
        print(return_list)
        return return_list

    def _closest_node_path(self, start, finish):
        """Finds the input and output node for two components that are closest\n
        Inputs: start_component(str), End_component(str)\n
        Returns: list{node, node}"""


        start_nodes = self._find_intake_nodes_with(start)
        finish_nodes = self._find_output_nodes_with(finish)
        closest_distance = 9999

        if ((len(start_nodes) == 0) or (len(finish_nodes) == 0)):
            sys.exit("Missing input or output connections. Aborting system.")
        #TODO This is not optimized for Multiport connections and honestly likely never will be (it will make cleaning function more complex)
        for start_point in start_nodes:
            for end_point in finish_nodes:
                if (abs(int(start_point)-int(end_point))) < closest_distance and int(start_point) < int(end_point):
                    closest_distance = abs(int(start_point)-int(end_point))
                    closest_nodes = [start_point, end_point]
        if(closest_distance == 9999):
            sys.exit(f"ERROR: PATH NOT FOUND BETWEEN {start} and {finish}. ABORTING PROGRAM.")
            return []
        else:
            return closest_nodes 
    
    def _is_hotplate_free(self, hotplate):
        """Used to verify if all used vials on a hotplate have completed.  Returns True if hotplate is available for reasignment"""

        is_free = True

        for component in self.components:
            if self.components[component]["type"] == "vial" and self.components[component]["hotplate"] == hotplate:
                if self.components[component]["used"] == True and self.components[component]["completed"] == False:
                    is_free = False
        
        return (is_free)

    def set_experiment_vial(self, name, requested_temperature=None, requested_stir_speed=None):
        """find an empty vial, change its name to the experiment measurement name, and update all search trees\n
        Returns already_heated, hotplatename, temperature\n
        TODO: need a way to mark a vial as done to free up hotplate"""
        
        selected_vial = None
        acceptable_vial = False

        #Return Values
        temp_to_return = None
        already_heated = False
        hotplate_name = None
        stir_to_return = requested_stir_speed #TODO Replace me with actual search function below when searching for hotplate

        lower_temp = requested_temperature - self.acceptable_hotplate_range
        upper_temp = requested_temperature + self.acceptable_hotplate_range
        found_vial = False
        for component in self.components:
            #These if statements are seperated to avoid checking for a used parameter on types that may not have one
            if self.components[component]["type"] == "vial":
                if self.components[component]["used"] == False:

                    


                    #Condition: Unused vial with acceptable temperature already set
                    if (self.components[component]["hotplate_temp"] != False) and (lower_temp <= self.components[component]["hotplate_temp"]) and (upper_temp >= self.components[component]["hotplate_temp"]):
                        acceptable_vial = True
                        selected_vial = component

                        hotplate_name = self.components[component]["hotplate"]
                        temp_to_return = self.components[component]["hotplate_temp"]
                        already_heated = True
                        break # We break here as this is the Ideal situation

                    #Condition: Unused vial on a hotplate that has a different temperature set, but has completed all its current reactions
                    elif((self.components[component]["hotplate_temp"] != False) and self._is_hotplate_free(self.components[component]["hotplate"])):
                        acceptable_vial = True
                        selected_vial = component
                        found_vial = True

                        hotplate_name = self.components[component]["hotplate"]
                        temp_to_return = requested_temperature
                        already_heated = False

                    #Condition: Unused Vial and unused hotplate, last resort
                    elif self.components[component]["hotplate_temp"] == False and acceptable_vial == False and not found_vial:
                        selected_vial = str(component)
                        acceptable_vial = True

                        hotplate_name = self.components[component]["hotplate"]
                        temp_to_return = requested_temperature
                        already_heated = False
                        
            
        if acceptable_vial:
            self.components[name] = self.components[selected_vial]
            del self.components[component]
            #self.components[name] = name #TODO EDITED
            #input(f"{self.components[name]}")
            self.components[name]["used"] = True

            self.components[name]["hotplate_temp"] = temp_to_return
            hotplate_name = self.components[name]["hotplate"]
            #Set Hotplate and rename all vials accordingly

        elif acceptable_vial == False:
            print("ERROR, NO VIALS CAN BE HEATED TO DESIRED TEMP. WITHOUT RUINING OTHER REACTIONS")

        self._update_nodes(self.components)
        return (already_heated, hotplate_name, temp_to_return, stir_to_return)
        
    def SetHotplate(self, hotplate_name, new_temperature):
        """Updates current temperatures for hotplates\n
        Inputs: hotplate name and temperature"""

        for component in self.components:
            #These if statements are seperated to avoid checking for a used parameter on types that may not have one
            if self.components[component]["type"] == "vial" and "hotplate" in self.components[component]:
                if self.components[component]["hotplate"] == hotplate_name:
                    self.components[component]["hotplate_temp"] = new_temperature
        self._update_nodes(self.components)
        
        

    def GetComponents(self):
        return self.components
    def _find_path(self, start, finish):
        """Returns list of valve-port pairs to set a path between two components"""
        #print(f"{start} -> {finish}")
        #If the desired path is a direct connection to a syringe pump, insta return
        if self.components[start]["type"] == "syringe_pump":
            if finish in self.components[start]["connections"]:
                return ([[start, self.components[start]["connections"].index(finish)+1]])
        elif self.components[finish]["type"] == "syringe_pump":
            if start in self.components[finish]["connections"]:
                return([[finish, self.components[finish]["connections"].index(start)+1]])
        #Old method
        """
        if((finish in self.components[start]["connections"]) and self.components[start]["type"] == "syringe_pump"):
            return ([[start, self.components[start]["connections"].index(finish)+1]])
        elif(start in self.components[finish]["connections"] and self.components[finish]["type"] == "syringe_pump"):
            return([[finish, self.components[finish]["connections"].index(start)+1]])
        """
        start_end = self._closest_node_path(start, finish)
        steps = int(start_end[1])-int(start_end[0])
        valve_path = []
  
        #First step, first node find connection to start device and append [1st node, device port]
        first_step = [int(start_end[0]),self.nodes[start_end[0]]["connections"].index(start)+1]
        valve_path.append(first_step)

        #last step Do the same as first step, append later
        last_step = [int(start_end[1]),self.nodes[start_end[1]]["connections"].index(finish)+1]

        #set syringe pump if target/start point is a syringe
        #URGENT TODO THIS IS BAD
        #Figure out how node tree determine if a valve is on a node, reverse engineer.
        if (self.components[start]["type"]=="syringe_pump"):
            #print(self.components[start]["connections"])
            valve_path.append([start, int(self.components[start]["connections"].index(str(first_step[0]))+1)]) #+1 to account for idx vs real pos.
        elif (self.components[finish]["type"]=="syringe_pump"):
            #print(self.components[finish]["connections"])
            valve_path.append([finish, int(self.components[finish]["connections"].index(str(last_step[0]))+1)])

        for node in range(int(start_end[0])+1,int(start_end[1])):
            step = [int(node), 1]
            valve_path.append(step)
        
        valve_path.append(last_step)

        return (valve_path)


    

