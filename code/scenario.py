# -*- coding: utf-8 -*-
"""
scenario.py
v1.4

project, scenario, network 
IFN-Transport: application of Ideal Flow Network for Transportation Network 

@author: Kardi Teknomo
http://people.revoledu.com/kardi/
"""
import IdealFlowNetwork as ifn
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json
import csv
import networkx as nx
import math


class Project():
    def __init__(self, file_path):
        # super().__init__()
        self.file_path = file_path  # project file name (including path

        # initialization
        self.scenarios = None
        self.folder_path = ""  # project folder
        self.project_data = ""  # JSON content of the project

        # load project JSON file
        if os.path.exists(file_path):
            self.folder_path = os.path.dirname(os.path.realpath(file_path))
            print("project path", self.folder_path)
            self.load_default(file_path)
            self.run_scenarios()

    def run_scenarios(self):
        # extract and run each scenario
        self.scenarios = self.extract_scenarios()
        for scn_id, dict_scenario in self.scenarios.items():
            scn = Scenario(scn_id, dict_scenario, self.folder_path)
            # scn.run_scenario()
            print(scn, '\n')

    def load_default(self, file_path):
        # load from project json file to fill self.project_data
        with open(file_path, 'r') as file:
            dic = json.load(file)
            self.project_data = dic["project"]  # project is the root

    def extract_scenarios(self):
        scenarios = {}
        for key, value in self.project_data.items():
            if key.startswith("scenario-"):
                scenarios[key] = value
        return scenarios


class Scenario():
    def __init__(self, id, dict_scenario, folder_path):
        self.dfLink = None
        self.nodeIds = None
        self.id = id  # scenario id
        self.dict_scenario = dict_scenario  # dictionary_scenario

        # initialize input values of a scenario
        self.name = ""
        self.folder_path = folder_path  # initial scenario folder assume to be the same as project folder
        self.description = ""  # string
        self.networks = None  # dictionary of networks
        self.model = None  # dictionary of model
        self.calibration = None  # dictionary of calibration model
        self.travel_cost_model = ""  # "BPR" or "Greenhields"
        self.travel_cost_model_parameters = None  # {'alpha': 15, 'beta': 4} for BPR; "Greenhields" has no external model parameter
        self.calibration_basis = ""  # "max-congestion", "total-flow", "real-flow"
        self.calibration_parameter = None
        """ choice of calibration_parameter
                {'max-allowable-congestion': 0.9},  # for "max-congestion"
                {'total-flow': 15000},              # for "total-flow"
                {'criterion':'SSE'},                # for "real-flow"
                {'criterion': 'R^2'}                # for "real-flow"
        """
        self.total_flow = None
        self.max_allowable_congestion = None
        self.data = None  # {"flow": "file path of real world flow data"}

        # initialize internal state values
        self.scalingFactor = 0

        # initial run: parse dictionary into internal values
        self.parse_scenario()
        self.run_scenario()

    def __str__(self):
        return "scenario id = " + str(self.id) + \
            "\nscenario name = " + str(self.name) + \
            "\nfolder = " + str(self.folder_path) + \
            "\ndescription = " + str(self.description) + \
            "\ntravel_cost = " + str(self.travel_cost_model) + \
            "\nmodel_parameters = " + str(self.travel_cost_model_parameters) + \
            "\ncalibration_basis = " + str(self.calibration_basis) + \
            "\ncalibration_parameter = " + str(self.calibration_parameter) + \
            "\ntotal_flow = " + str(self.total_flow) + \
            "\nmax_allowable_congestion = " + str(self.max_allowable_congestion) + \
            "\ndata = " + str(self.data)

    def run_scenario(self):
        self.runScenario()

    def parse_scenario(self):
        """
        a scenario consists of networks, model and optionally data
        here we fill up the properties of this scenario object
        """
        # extract scenario name (if specified by user)
        if "name" in self.dict_scenario:
            self.name = self.dict_scenario["name"]

        # extract folder name (if specified by user)
        # if not use project folder as default
        if "folder" in self.dict_scenario:
            self.folder_path = self.dict_scenario["folder"]
        print('scenario folder = ', self.folder_path)

        # extract description
        if "description" in self.dict_scenario:
            self.description = self.dict_scenario["description"]

        # extract networks
        self.extract_networks_from_scenario()
        self.dfLink = self.networks['network-0'].dfLink

        # extract model
        self.extract_model_from_scenario()

        # extract data
        if "data" in self.dict_scenario:
            self.data = self.dict_scenario["data"]

    def extract_networks_from_scenario(self):
        networks = {}
        for key, value in self.dict_scenario.items():
            if key.startswith("network-"):
                net = Network(key, value, self.folder_path)
                networks[key] = net
                print(net, '\n')
        self.networks = networks
        return networks

    def extract_model_from_scenario(self):
        # extract model
        if "model" in self.dict_scenario:
            self.model = self.dict_scenario["model"]

            if "travel-cost" in self.model:
                self.travel_cost_model = self.model["travel-cost"]

            if "travel-cost-parameters" in self.model:
                self.travel_cost_model_parameters = self.model["travel-cost-parameters"]

            if "calibration" in self.model:
                self.calibration = self.model["calibration"]

                if "calibration-basis" in self.calibration:
                    self.calibration_basis = self.calibration["calibration-basis"]

                if "calibration-parameter" in self.calibration:
                    self.calibration_parameter = self.calibration["calibration-parameter"]

                    if "total-flow" in self.calibration_parameter:
                        self.total_flow = self.calibration_parameter["total-flow"]
                    if "max-allowable-congestion" in self.calibration_parameter:
                        self.max_allowable_congestion = self.calibration_parameter["max-allowable-congestion"]

    def runScenario(self):
        C = self.mLink2WeightedAdjacency(field='Capacity')  # capacity
        S = ifn.capacity2stochastic(C)  # Markov stochastic
        if not ifn.isIrreducible(S):
            print("Your network is not strongly connected. Clean the network data either by finding the largest "
                  "strongly connected component or add a cloud node and dummy links.")
            return None

        # first try at kappa=1
        pi = ifn.markov(S, kappa=1)  # node values
        F = ifn.idealFlow(S, pi)  # ideal flow
        G = ifn.hadamardDivision(F, C)  # congestion
        maxCongestion = np.max(G)

        kappa = 1
        if self.calibration_basis == "total-flow":
            # calibrate with new kappa to reach totalFlow
            kappa = self.total_flow
        elif self.calibration_basis == "max-congestion":
            # calibrate with new kappa to reach max congestion level
            kappa = float(self.max_allowable_congestion) / maxCongestion  # total flow
        elif self.calibration_basis == "real-flow":
            self.find_optimum_scaling()
            self.total_flow = np.sum(ifn.sumOfRow(F))
            kappa = self.total_flow*self.scalingFactor

        # compute ideal flow and congestion
        # scaling=ifn.globalScaling(F,'min',1)
        # F1=ifn.equivalentIFN(F, scaling)
        F1 = ifn.equivalentIFN(F, kappa)
        # pi=ifn.markov(S,kappa)               # node values
        # F3=ifn.idealFlow(S,pi)               # scaled ideal flow
        G = ifn.hadamardDivision(F1, C)  # congestion
        maxCongestion = np.max(G)

        # compute link performances
        self.addField2dfLink(G, 'Congestion')
        self.addField2dfLink(F, "BasisFlow")
        self.addField2dfLink(F1, "EstFlow")
        self.computeLinkPerformance()

        # save output mLink
        dfLink_file_name = os.path.join(self.folder_path, self.id + ".csv")
        self.dfLink.to_csv(dfLink_file_name, quoting=csv.QUOTE_NONNUMERIC)

        # network performance
        avgSpeed = np.nanmean(self.dfLink['Speed'])
        avgTravelTime = np.nanmean(self.dfLink['TravelTime'])
        avgDelay = np.nanmean(self.dfLink['Delay'])
        avgDist = np.nanmean(self.dfLink['Distance'])

        # report
        report = (str(self.__str__()) + \
                  "\n\n" + str(self.networks['network-0']) + \
                  "\n\nNetwork performance:\n" + \
                  "\tTotal Flow = " + str(round(kappa, 2)) + " pcu/hour" + "\n" + \
                  "\tMax Congestion = " + str(round(maxCongestion, 4)) + "\n" + \
                  "\tAvg Link Speed =" + str(round(avgSpeed, 4)) + " km/hour\n" + \
                  "\tAvg Link Travel Time = " + str(round(60 * avgTravelTime / avgDist, 4)) + " min/km\n" + \
                  "\tAvg Link Delay = " + str(round(3600 * avgDelay / avgDist, 4)) + " seconds/km\n" + \
                  "Basis:\n" + \
                  "\tAvg Link Distance = " + str(round(avgDist, 4)) + " m/link\n" + \
                  "\tAvg Link Travel Time = " + str(round(3600 * avgTravelTime, 4)) + " seconds/link\n" + \
                  "\tAvg Link Delay = " + str(round(3600 * avgDelay, 4)) + " seconds/link\n")
        print(report)
        # save network performance
        report_file_name = os.path.join(self.folder_path, self.id + ".net")
        with open(report_file_name, 'w') as fh:
            fh.write(report)  # i

        plt = self.networks['network-0'].display_network('Congestion')  # display network congestion
        plt.show()

    def addField2dfLink(self, F, field):
        """
        update self.dfLink with additional column about matrix F.
        Matrix F size must be n by n, where n is number of nodes
        """
        if not self.nodeIds:
            # get unique node IDs from second and third fields of mLink
            self.nodeIds = list(np.union1d(self.dfLink.Node1, self.dfLink.Node2))

        mR, mC = self.dfLink.shape
        arrF = []
        for index, row in self.dfLink.iterrows():
            r = self.nodeIds.index(row.Node1)
            c = self.nodeIds.index(row.Node2)
            v = F[r - 1, c - 1]
            arrF.append(v)
        self.dfLink[field] = arrF



    def computeLinkPerformance(self):
        """
        return mLink with additional link performance

        """
        travelTimeModel = self.travel_cost_model
        cloudNode = self.networks['network-0'].cloud_node_id
        mR, mC = self.dfLink.shape
        arrSpeed = []
        arrTravelTime = []
        arrDelay = []
        for index, row in self.dfLink.iterrows():
            node1 = row.Node1
            node2 = row.Node2
            if cloudNode is not None and (cloudNode == str(node1) or cloudNode == str(node2)):
                speed = np.nan  # v
                travelTime = np.nan  # t
                minTravelTime = np.nan  # t0
                delay = np.nan  # delta
            else:
                maxSpeed = row.MaxSpeed  # u in km/hour
                dist = row.Distance  # d in km; mLink[4,j] in km
                congestion = row.Congestion  # g

                if travelTimeModel == 'Greenshield':
                    # based on greenshield
                    if congestion <= 1:
                        speed = maxSpeed / 2 * (1 + math.sqrt(1 - congestion))  # v in km/hour
                        if speed > 0:
                            travelTime = dist / speed  # t   in hour
                        else:
                            travelTime = np.inf
                        if maxSpeed > 0:
                            minTravelTime = dist / maxSpeed  # t0  in hour
                        else:
                            minTravelTime = np.inf
                        delay = travelTime - minTravelTime  # delta in hour
                    else:
                        speed = 0
                        travelTime = np.inf
                        minTravelTime = np.inf
                        delay = np.inf
                else:
                    # based on BPR (by default)
                    minTravelTime = dist / maxSpeed  # t0  in hour
                    travelTime = minTravelTime * (1 + 15 * congestion ** 4)  # t in hour
                    if travelTime > 0:
                        speed = dist / travelTime  # v  in km/hour
                    else:
                        speed = 0
                    delay = travelTime - minTravelTime  # delta in hour

            arrSpeed.append(speed)
            arrTravelTime.append(travelTime)
            arrDelay.append(delay)

        self.dfLink['Speed'] = arrSpeed
        self.dfLink['TravelTime'] = arrTravelTime
        self.dfLink['Delay'] = arrDelay

    def isStronglyConnectedNetwork(self):
        C = self.mLink2WeightedAdjacency(field='Capacity')  # capacity
        S = ifn.capacity2stochastic(C)  # Markov stochastic
        if ifn.isIrreducible(S):
            return "Your network is strongly connected."
        else:
            return "Your network is not strongly connected. Clean the network data either by finding the largest " \
                   "strongly connected component or add a cloud node and dummy links."

    def mLink2WeightedAdjacency(self, field='Capacity'):
        """
        return capacity matrix (by default)
        but depending on the fieldNo, it can also return Dist,Lanes,MaxSpeed

        assume fields in mLink at least contain
            LinkID,Node1,Node2,Capacity,Dist,MaxSpeed,....

        """
        mLink = self.networks['network-0'].dfLink
        # get unique node IDs from second and third fields of mLink
        self.nodeIds = list(np.union1d(mLink.Node1, mLink.Node2))
        n = np.prod(len(self.nodeIds))
        A = np.zeros((n, n), dtype=np.float64)
        # fill up with 1 when there is a link
        coord = zip(mLink.Node1, mLink.Node2, mLink[field])
        for item in coord:
            (node1, node2, k) = item
            r = self.nodeIds.index(node1)
            c = self.nodeIds.index(node2)
            A[int(r) - 1, int(c) - 1] = float(k)
        return A

    def findOptScaling(self):
        """
        search for optimal scaling factor

        Returns
        -------
        opt_scaling : float
            optimal scaling factor
        opt_Rsq : float
            R^2 at optimal scaling
        dicRsq : dictionary             to compute R^2
        dicSSE : dictionary             to compute SSE
        SST : float
            Sum Square Total (to be used to compute R^2)

        """
        # get real flow data
        real_flow_file_name = self.data["flow"]
        dfFlow = pd.read_csv(os.path.join(self.folder_path, real_flow_file_name), index_col='LinkID')

        # Check if all links in actual flow match the link file
        for linkID, row in dfFlow.iterrows():
            a_link = self.dfLink.loc[linkID]
            if not (a_link.Node1 == row.Node1 and a_link.Node2 == row.Node2):
                return None

        if "BasisFlow" not in self.dfLink:
            C = self.mLink2WeightedAdjacency(field='Capacity')
            F = ifn.capacity2idealFlow(C)
            self.addField2dfLink(F, "BasisFlow")

        avgScale = 0
        count = 0
        avgFlow = 0
        for linkID, row in dfFlow.iterrows():
            basis = self.dfLink["BasisFlow"].loc[linkID]
            flow = row["ActualFlow"]
            scaling = flow / basis
            count = count + 1
            avgScale = (count - 1) / count * avgScale + scaling / count
            avgFlow = (count - 1) / count * avgFlow + flow / count
            # print('linkID',linkID,'basis',basis,'flow',flow,'scaling',scaling,'avgScale',avgScale)

        SST = 0
        for linkID, row in dfFlow.iterrows():
            flow = row["ActualFlow"]
            SST = SST + math.pow(flow - avgFlow, 2)
        # print('SST',SST)

        dicSSE = {}
        dicRsq = {}
        for scale in range(int(avgScale) - 2500, int(avgScale) + 2500):
            SSE = 0
            for linkID, row in dfFlow.iterrows():
                basis = self.dfLink["BasisFlow"].loc[linkID]
                flow = row["ActualFlow"]
                estFlow = scale * basis
                sqErr = math.pow(flow - estFlow, 2)
                SSE = SSE + sqErr
            if SST > 0:
                Rsq = 1 - SSE / SST
            else:
                Rsq = 1  # actually undefined when SST=1 (i.e. only one data)
            dicRsq[scale] = Rsq
            dicSSE[scale] = SSE

        # opt_scaling = max(dicRsq, key=dicRsq.get)
        # opt_Rsq = dicRsq[opt_scaling]
        opt_scaling = min(dicSSE, key=dicSSE.get)
        opt_SSE = dicSSE[opt_scaling]
        return opt_scaling, opt_SSE, dicRsq, dicSSE, SST

    def find_optimum_scaling(self):
        opt_scaling, opt_SSE, dicRsq, dicSSE, SST = self.findOptScaling()
        self.scalingFactor = opt_scaling

        # if self.calibration_parameter["criterion"] == "R^2":
        x = dicRsq.keys()
        y = dicRsq.values()
        opt_scale = max(dicRsq, key=dicRsq.get)
        opt_Rsq = dicRsq[opt_scale]
        plt.figure()
        plt.plot(x, y, opt_scale, opt_Rsq, 'or')
        plt.xlabel("scaling")
        plt.ylabel("R-Square")
        # if self.calibration_parameter["criterion"] == "SSE":
        # SSE plot
        plt.figure()
        x = dicSSE.keys()
        y = dicSSE.values()
        opt_scale = min(dicSSE, key=dicSSE.get)
        optSSE = dicSSE[opt_scale]
        plt.plot(x, y, opt_scale, optSSE, 'or')
        plt.xlabel("scaling")
        plt.ylabel("SSE")
        # print(opt_scaling, opt_SSE)
        # print('Optimum scaling = ' + str(opt_scaling) + '; Optimum R-square = ' + str(round(opt_Rsq, 4)))
        print('Optimum scaling = ' + str(opt_scaling) + '; Min-SSE = ' + str(round(opt_SSE, 4)))


class Network():
    def __init__(self, id, dict_network, folder_path):
        self.id = id  # network-#
        self.dict_network = dict_network  # dictionary_network

        # initialize input values of a network
        self.folder_path = folder_path  # initial network folder = scenario folder
        self.description = ""  # string
        self.name = ""
        self.node_file_name = ""
        self.link_file_name = ""
        self.graph_file_name = ""
        self.cloud_node_id = ""
        self.network_weight = 1
        self.nodeIds = None
        self.dfLink = None
        self.dfNode = None

        # initial command
        self.parse_network_dictionary()

    def __str__(self):
        return "\tnetwork id = " + str(self.id) + \
            "\n\tnetwork name = " + str(self.name) + \
            "\n\tfolder = " + str(self.folder_path) + \
            "\n\tdescription = " + str(self.description) + \
            "\n\tnode_file_name = " + str(self.node_file_name) + \
            "\n\tlink_file_name = " + str(self.link_file_name) + \
            "\n\tgraph_file_name = " + str(self.graph_file_name) + \
            "\n\tcloud_node_id = " + str(self.cloud_node_id) + \
            "\n\tnetwork_weight = " + str(self.network_weight)

    def parse_network_dictionary(self):
        """
        a scenario consists of networks, model and optionally data
        here we fill up the properties of this scenario object
        """
        # extract folder name (if specified by user in JSON)
        if "folder" in self.dict_network:
            self.folder_path = self.dict_network["folder"]

        # extract description
        if "description" in self.dict_network:
            self.description = self.dict_network["description"]

        # extract name
        if "name" in self.dict_network:
            self.name = self.dict_network["name"]

        # extract node_file_name
        if "node" in self.dict_network:
            self.node_file_name = self.dict_network["node"]
            node_file_name = os.path.join(self.folder_path, self.node_file_name)
            print("loading nodes:", node_file_name)
            self.dfNode = pd.read_csv(node_file_name, index_col='NodeID')

        # extract link_file_name
        if "link" in self.dict_network:
            self.link_file_name = self.dict_network["link"]
            link_file_name = os.path.join(self.folder_path, self.link_file_name)
            print("loading links:", link_file_name)
            self.dfLink = pd.read_csv(link_file_name, index_col='LinkID')

        # extract graph_file_name
        if "graph" in self.dict_network:
            self.graph_file_name = self.dict_network["graph"]

        # extract cloud_node_id
        if "cloud" in self.dict_network:
            self.cloud_node_id = self.dict_network["cloud"]

        # extract network_weight
        if "weight" in self.dict_network:
            self.network_weight = self.dict_network["weight"]
        else:
            self.network_weight = 1

    def display_network(self, field='Capacity'):
        """
        display network based on field in self.dfLink
        and node coordinate in self.dfNode

        Parameters
        ----------
        field : string, optional
            field in self.dfLink. The default is 'Capacity'.

        Returns
        -------
        plt : plot


        """
        plt.figure()
        G = nx.DiGraph()

        maxFieldValue = max(self.dfLink[field])
        for index, row in self.dfNode.iterrows():
            if self.cloud_node_id != index:
                x = row.X
                y = row.Y
                G.add_node(index, pos=(x, y))
        for index, row in self.dfLink.iterrows():

            node1 = row.Node1
            node2 = row.Node2
            if self.cloud_node_id != node1 and self.cloud_node_id != node2:
                weight = (maxFieldValue - row[field]) * 100

                G.add_edge(node1, node2, weight=weight)

        pos = nx.get_node_attributes(G, 'pos')  # node position

        # edges
        edges, weights = zip(*nx.get_edge_attributes(G, 'weight').items())
        nx.draw(G, pos, node_color='w', edgelist=edges, edge_color=weights, width=1.0, edge_cmap=plt.cm.RdYlGn)

        # nodes
        nodes = nx.draw_networkx_nodes(G, pos, node_color='w', node_size=3)
        nodes.set_edgecolor('b')

        plt.axis('off')
        return plt


if __name__ == '__main__':
    # sample usage
    folder = r"..\..\IFN14\GitHub\projects\Triangle"
    project_file_name = "triangle.json"
    file_path = os.path.join(folder, project_file_name)
    prj = Project(file_path)
