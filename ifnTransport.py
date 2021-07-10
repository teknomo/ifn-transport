# -*- coding: utf-8 -*-
"""
ifn-transport.py

Traffic Assignment based on Ideal Flow Network

@author: Kardi Teknomo
https://people.revoledu.com/kardi/
v0.1
"""
import numpy as np
import math
import os
import sys
import IdealFlowNetwork as ifn
import pandas as pd
import csv
import matplotlib.pyplot as plt
import networkx as nx


class IFN_Transport():
    def __init__(self, scenario):
        self.readScenario(scenario)
        
        C=self.mLink2WeightedAdjacency(field='Capacity') # capacity
        S=ifn.capacity2stochastic(C)               # Markov stochastic
       
        # first try at arbitrary kappa=100
        pi=ifn.steadyStateMC(S,kappa=100)          # node values
        F=ifn.idealFlow(S,pi)                      # ideal flow
        G=self.HadamardDivision(F,C)               # congestion
        maxCongestion=np.max(G)

        if self.calibrationBasis=="flow":
            # calibrate with new kappa to reach totalFlow
            kappa=self.totalFlow
        else: # calibrationBasis=="congestion"
            # calibrate with new kappa to reach max congestion level
            kappa=100*float(self.maxAllowableCongestion)/maxCongestion # total flow

        # compute ideal flow and congestion
        pi=ifn.steadyStateMC(S,kappa)                         # node values
        F=ifn.idealFlow(S,pi)                                 # scaled ideal flow
        G=self.HadamardDivision(F,C)                               # congestion
        maxCongestion=np.max(G)

        # compute link performances
        self.addField2dfLink(F,'Flow') # fieldNo=7 flow
        self.addField2dfLink(G,'Congestion') # fieldNo=8 congestion level
        self.computeLinkPerformance() # fieldNo=9 to 11
    
        # save output mLink
        self.dfLink.to_csv(self.folder+self.scenarioName+'.csv',quoting=csv.QUOTE_NONNUMERIC)
        
        # network performance
        avgSpeed=np.nanmean(self.dfLink['Speed'])
        avgTravelTime=np.nanmean(self.dfLink['TravelTime'])
        avgDelay=np.nanmean(self.dfLink['Delay'])
        avgDist=np.nanmean(self.dfLink['Distance'])
       
        # report
        report=self.scenarioName+"\n"+\
            "Network performance:\n"+\
            "\tTotal Flow = "+ str(round(kappa,2))+" pcu/hour"+"\n"+\
            "\tMax Congestion = "+str(round(maxCongestion,4))+"\n"+\
            "\tAvg Link Speed ="+str(round(avgSpeed,4))+" km/hour\n"+\
            "\tAvg Link Travel Time = "+str(round(1000*60*avgTravelTime/avgDist,4))+" min/km\n"+\
            "\tAvg Link Delay = "+str(round(1000*3600*avgDelay/avgDist,4))+ " seconds/km\n"+\
            "Basis:\n"+\
            "\tAvg Link Distance = "+str(round(avgDist,4))+ " m/link\n"+\
            "\tAvg Link Travel Time = "+str(round(3600*avgTravelTime,4))+" seconds/link\n"+\
            "\tAvg Link Delay = "+str(round(3600*avgDelay,4))+ " seconds/link\n"
        print(report)        
        # save network performance
        with open(self.folder+self.scenarioName+'.net', 'w') as fh:
            fh.write(report)              # i
            
        
        plt=self.display_network('Congestion') # display network congestion
        plt.show()


    def readScenario(self,scenario):
        '''
        parse scenario, read node file and link file
        return node matrix and link matrix
        the fields are in rows
        '''
        # initialize the default values
        self.travelTimeModel=None
        self.maxAllowableCongestion=1
        self.totalFlow=1000
        self.calibrationBasis=None
        self.cloudNode=None
        self.capacityBasis=None
        
        # read scenario
        self.folder=os.path.dirname(scenario)
        if self.folder!="":
            self.folder=self.folder+"\\"
        lines=open(scenario,"r").read().splitlines()

        # parsing scenario
        for item in lines:
            (lhs,rhs)=item.split('=')
            if lhs=='ScenarioName':
                self.scenarioName=rhs
            if lhs=='Node':
                self.dfNode=pd.read_csv(self.folder+rhs,index_col='NodeID')
            if lhs=="Link":
                self.dfLink=pd.read_csv(self.folder+rhs,index_col='LinkID')
            if lhs=='maxAllowableCongestion':
                self.maxAllowableCongestion=rhs
            if lhs=='travelTimeModel':
                self.travelTimeModel=rhs
            if lhs=='totalFlow':
                self.totalFlow=float(rhs)
            if lhs=='calibrationBasis':
                self.calibrationBasis=rhs
            if lhs=='cloudNode':
                self.cloudNode=rhs
            if lhs=='capacityBasis':
                self.capacityBasis=rhs


    def HadamardDivision(self,A,B):
        '''
        return A./B with agreement 0/0=0
        '''
        B[B==0]=np.inf        
        return np.divide(A,B)


    def addField2dfLink(self,F,field):
        '''
        update self.dfLink with additional column about matrix F
        matrix F size must be n by n, where n is number of nodes
        '''
        mR,mC=self.dfLink.shape
        arrF=[]
        for index, row in self.dfLink.iterrows():
            r=int(row.Node1)
            c=int(row.Node2)
            v=F[r-1,c-1]
            arrF.append(v)
        self.dfLink[field]=arrF        
    

    def computeLinkPerformance(self):
        '''
        return mLink with additional link performance
        
        '''
        travelTimeModel=self.travelTimeModel
        cloudNode=self.cloudNode
        mR,mC=self.dfLink.shape
        arrSpeed=[]
        arrTravelTime=[]
        arrDelay=[]
        for index, row in self.dfLink.iterrows():
            node1=row.Node1
            node2=row.Node2
            if cloudNode is not None and (cloudNode==str(node1) or cloudNode==str(node2)):
                speed=np.nan            # v
                travelTime=np.nan       # t
                minTravelTime=np.nan    # t0
                delay=np.nan            # delta
            else:
                maxSpeed=row.MaxSpeed     # u in km/hour
                dist=row.Distance/1000    # d in km; mLink[4,j] in meter
                congestion=row.Congestion  # g

                if travelTimeModel=='Greenshield':
                    # based on greenshield
                    speed=maxSpeed/2*(1+math.sqrt(1-congestion)) # v in km/hour
                    if speed>0:
                        travelTime=dist/speed       # t   in hour
                    else:
                        travelTime=0
                    if maxSpeed>0:
                        minTravelTime=dist/maxSpeed # t0  in hour
                    else:
                        minTravelTime=0
                    delay=travelTime-minTravelTime # delta in hour
                else:
                    # based on BPR (by default)
                    minTravelTime=dist/maxSpeed    # t0  in hour
                    travelTime=minTravelTime*(1+0.15*congestion**4) # t in hour
                    if travelTime>0:
                        speed=dist/travelTime          # v  in km/hour
                    else:
                        speed=0
                    delay=travelTime-minTravelTime # delta in hour
                
            arrSpeed.append(speed)
            arrTravelTime.append(travelTime)
            arrDelay.append(delay)
        
        self.dfLink['Speed']=arrSpeed
        self.dfLink['TravelTime']=arrTravelTime
        self.dfLink['Delay']=arrDelay
        
    
    def mLink2WeightedAdjacency(self,field='Capacity'):
        '''
        return capacity matrix (by default)
        but depending on the fieldNo, it can also return Dist,Lanes,MaxSpeed
        
        assume fields in mLink at least contain
            LinkID,Node1,Node2,Capacity,Dist,MaxSpeed,....
        
        '''
        mLink=self.dfLink
        # get unique node IDs from second and third fields of mLink
        nodeIds=np.union1d(mLink.Node1,mLink.Node2)
        n=np.prod(nodeIds.shape)
        del nodeIds # to save memory
        
        A=np.zeros((n,n), dtype=np.float64)
        # fill up with 1 when there is a link
        coord=zip(mLink.Node1,mLink.Node2,mLink[field])
        for item in coord:
            (r,c,k)=item
            A[int(r)-1,int(c)-1]=float(k)
        return A

    def display_network(self,field='Capacity'):
        '''
        display network based on field in self.dfLink
        and node coordinate in self.dfNode

        Parameters
        ----------
        field : string, optional
            field in self.dfLink. The default is 'Capacity'.

        Returns
        -------
        plt : plot
            

        '''
        
        G = nx.DiGraph()
        
        maxFieldValue=max(self.dfLink[field])
        for index, row in self.dfNode.iterrows():
            x=row.X
            y=row.Y
            G.add_node(index,pos=(x,y))
        for index, row in self.dfLink.iterrows():
            node1=int(row.Node1)
            node2=int(row.Node2)
            weight=(maxFieldValue-row[field])*100
            # weight=row[field]
            G.add_edge(node1, node2, weight=weight)
        
        pos = nx.get_node_attributes(G,'pos') # node position
    
        # edges
        edges,weights = zip(*nx.get_edge_attributes(G,'weight').items())
        nx.draw(G, pos, node_color ='w', edgelist=edges, edge_color=weights, width=1.0, edge_cmap=plt.cm.RdYlGn)
        
        # nodes
        nodes=nx.draw_networkx_nodes(G, pos, node_color ='w', node_size=3) 
        nodes.set_edgecolor('b')
        
        plt.axis('off')
        return plt


if __name__ == '__main__':
    if len(sys.argv)>1:
        scenario = sys.argv[1]
        if scenario=="":
            print("to use: input the scenario file (including the folder name)")
    else:
        scenario='Scenario.scn'
    IFN_Transport(scenario)
    