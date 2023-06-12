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
    def __init__(self, scenarioFName):
        self.readScenario(scenarioFName)
        

    def runScenario(self):
        C=self.mLink2WeightedAdjacency(field='Capacity') # capacity
        S=ifn.capacity2stochastic(C)               # Markov stochastic
        if not ifn.isIrreducible(S):
            print("Your network is not strongly connected. Clean the network data either by finding the largest strongly connected component or add a cloud node and dummy links.")
            return None

        # first try at kappa=1
        pi=ifn.markov(S,kappa=1)          # node values
        F=ifn.idealFlow(S,pi)                      # ideal flow
        G=ifn.hadamardDivision(F,C)               # congestion
        maxCongestion=np.max(G)
        
        if self.calibrationBasis=="totalFlow":
            # calibrate with new kappa to reach totalFlow
            kappa=self.totalFlow
        elif self.calibrationBasis=="maxCongestion":
            # calibrate with new kappa to reach max congestion level
            kappa=float(self.maxAllowableCongestion)/maxCongestion # total flow
        elif self.calibrationBasis=="realFlow":
            kappa=self.scalingFactor
        
        # compute ideal flow and congestion
        # scaling=ifn.globalScaling(F,'min',1)        
        # F1=ifn.equivalentIFN(F, scaling)
        F1=ifn.equivalentIFN(F, kappa)
        # pi=ifn.markov(S,kappa)               # node values
        # F3=ifn.idealFlow(S,pi)                       # scaled ideal flow
        G=ifn.hadamardDivision(F1,C)                # congestion
        maxCongestion=np.max(G)
        
        # compute link performances
        self.addField2dfLink(G,'Congestion') 
        self.addField2dfLink(F,"BasisFlow")
        self.addField2dfLink(F1,"EstFlow")
        self.computeLinkPerformance() 
        
    
        # save output mLink
        self.dfLink.to_csv(self.folder+self.scenarioFileName+".csv",quoting=csv.QUOTE_NONNUMERIC)
        
        # network performance
        avgSpeed=np.nanmean(self.dfLink['Speed'])
        avgTravelTime=np.nanmean(self.dfLink['TravelTime'])
        avgDelay=np.nanmean(self.dfLink['Delay'])
        avgDist=np.nanmean(self.dfLink['Distance'])
       
        # report
        report=self.scenarioFileName+"\n"+\
            "Network performance:\n"+\
            "\tTotal Flow = "+ str(round(kappa,2))+" pcu/hour"+"\n"+\
            "\tMax Congestion = "+str(round(maxCongestion,4))+"\n"+\
            "\tAvg Link Speed ="+str(round(avgSpeed,4))+" km/hour\n"+\
            "\tAvg Link Travel Time = "+str(round(60*avgTravelTime/avgDist,4))+" min/km\n"+\
            "\tAvg Link Delay = "+str(round(3600*avgDelay/avgDist,4))+ " seconds/km\n"+\
            "Basis:\n"+\
            "\tAvg Link Distance = "+str(round(avgDist,4))+ " m/link\n"+\
            "\tAvg Link Travel Time = "+str(round(3600*avgTravelTime,4))+" seconds/link\n"+\
            "\tAvg Link Delay = "+str(round(3600*avgDelay,4))+ " seconds/link\n"
        print(report)        
        # save network performance
        with open(self.folder+self.scenarioFileName+'.net', 'w') as fh:
            fh.write(report)              # i
            
        plt=self.display_network('Congestion') # display network congestion
        plt.show()


    def readScenario(self,scenario):
        '''
        parse scenario, read node file and link file
        return node matrix and link matrix
        the fields are in rows
        '''
        if scenario=="":
            return 0
        
        # initialize the default values
        self.travelTimeModel=None
        self.maxAllowableCongestion=1
        self.totalFlow=10000
        self.calibrationBasis=None
        self.cloudNode=None
        self.capacityBasis=None
        
        # read scenario
        self.folder=os.path.dirname(scenario)
        if self.folder!="":
            self.folder=self.folder+"\\"
        lines=open(scenario,"r").read().splitlines()
        base=os.path.basename(scenario)
        self.scenarioFileName=os.path.splitext(base)[0] # scn filename without extension

        # parsing scenario
        for item in lines:
            if "=" in item:
                (lhs,rhs)=item.split('=')
                if lhs=='ScenarioName':
                    self.scenarioName=rhs
                if lhs=='Node':
                    self.dfNode=pd.read_csv(self.folder+rhs,index_col='NodeID')
                if lhs=="Link":
                    self.dfLink=pd.read_csv(self.folder+rhs,index_col='LinkID')
                # if lhs=="Output":
                #     self.outputFileName=rhs
                if lhs=='maxAllowableCongestion':
                    self.maxAllowableCongestion=rhs
                if lhs=='travelTimeModel':
                    self.travelTimeModel=rhs
                if lhs=='totalFlow':
                    self.totalFlow=float(rhs)
                if lhs=='scalingFactor':
                    self.scalingFactor=float(rhs)
                if lhs=='calibrationBasis':
                    self.calibrationBasis=rhs
                if lhs=='cloudNode':
                    self.cloudNode=rhs
                if lhs=='capacityBasis':
                    self.capacityBasis=rhs


    # def HadamardDivision(self,A,B):
    #     '''
    #     return A./B with agreement 0/0=0
    #     '''
    #     B[B==0]=np.inf        
    #     return np.divide(A,B)


    def addField2dfLink(self,F,field):
        '''
        update self.dfLink with additional column about matrix F
        matrix F size must be n by n, where n is number of nodes
        '''
        if not self.nodeIds:
            # get unique node IDs from second and third fields of mLink
            self.nodeIds = list(np.union1d(self.dfLink.Node1, self.dfLink.Node2))

        mR,mC=self.dfLink.shape
        arrF=[]
        for index, row in self.dfLink.iterrows():
            r=self.nodeIds.index(int(row.Node1))
            c=self.nodeIds.index(int(row.Node2))
            v=F[r-1,c-1]
            arrF.append(v)
        self.dfLink[field]=arrF        
    

    def findOptScaling(self,linkFName,realFlowFName):
        '''
        search for optimal scaling factor

        Parameters
        ----------
        linkFName : string
            link input file name
        realFlowFName : string
            real flow file name

        Returns
        -------
        opt_scaling : float
            optimal scaling factor
        opt_Rsq : float
            R^2 at optimal scaling
        dicRsq : dictionary
            dictionary to compute R^2
        dicSSE : dictionary
            dictionary to compute SSE
        SST : float
            Sum Square Total (to be used to compute R^2)

        '''
        # dfLink=pd.read_csv(linkFName,index_col='LinkID')
        dfFlow=pd.read_csv(realFlowFName,index_col='LinkID')
        
        # Check if all links in actual flow match the link file
        for linkID, row in dfFlow.iterrows():
            a_link=self.dfLink.loc[linkID]
            if not (a_link.Node1==row.Node1 and a_link.Node2==row.Node2):
                return None

        if "BasisFlow" not in self.dfLink:
            C=self.mLink2WeightedAdjacency(field='Capacity')
            F=ifn.capacity2idealFlow(C)
            scaling=ifn.globalScaling(F,'min',1)
            F1=ifn.equivalentIFN(F, scaling)
            self.addField2dfLink(F1,"BasisFlow")
        
        avgScale=0
        count=0
        avgFlow=0
        for linkID, row in dfFlow.iterrows():
            basis=self.dfLink["BasisFlow"].loc[linkID]
            flow=row["ActualFlow"]
            scaling=flow/basis
            count=count+1
            avgScale=(count-1)/count*avgScale+scaling/count
            avgFlow=(count-1)/count*avgFlow+flow/count
            # print('linkID',linkID,'basis',basis,'flow',flow,'scaling',scaling,'avgScale',avgScale)
        
            
        # print('SST',SST)
        SST=0
        dicSSE={}
        dicRsq={}
        for scale in range(int(avgScale)-50,int(avgScale)+50):
            SSE=0
            for linkID, row in dfFlow.iterrows():
                basis=self.dfLink["BasisFlow"].loc[linkID]
                flow=row["ActualFlow"]
                estFlow=scale*basis
                SST=SST+math.pow(flow-avgFlow,2)
                sqErr=math.pow(flow-estFlow,2)
                SSE=SSE+sqErr
            Rsq=1-SSE/SST
            dicRsq[scale]=Rsq
            dicSSE[scale]=SSE
                        
        opt_scaling = max(dicRsq, key=dicRsq.get)
        opt_Rsq=dicRsq[opt_scaling]
        return opt_scaling,opt_Rsq,dicRsq,dicSSE,SST


    # def calibrate(self,linkFName,opt_scaling):
    #     '''
    #     calibrate based on real flow

    #     Parameters
    #     ----------
    #     linkFName : string
    #         link input file name
    #     opt_scaling : float
    #         get the optimzal scaling from self.findOptScaling

    #     Returns
    #     -------
    #     dfLink : df link
    #         pandas datafame of link with additional fields
    #         of BasisFlow, EstFlow,Congestion

    #     '''
    #     dfLink=pd.read_csv(linkFName,index_col='LinkID')
        
    #     C=self.mLink2WeightedAdjacency(dfLink)        
    #     F=ifn.capacity2idealFlow(C)        
    #     scaling=ifn.globalScaling(F,'int')        
    #     F1=ifn.equivalentIFN(F, scaling)
    #     F2=ifn.equivalentIFN(F1, opt_scaling)
    #     G=ifn.hadamardDivision(F2,C)
    #     dfLink=self.addField2dfLink(dfLink,F1,"BasisFlow")
    #     dfLink=self.addField2dfLink(dfLink,F2,"EstFlow")
    #     dfLink=self.addField2dfLink(dfLink,G,'Congestion')
        
    #     return dfLink


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
                maxSpeed=row.MaxSpeed   # u in km/hour
                dist=row.Distance       # d in km; mLink[4,j] in km
                congestion=row.Congestion  # g

                if travelTimeModel=='Greenshield':
                    # based on greenshield
                    if congestion<=1:
                        speed=maxSpeed/2*(1+math.sqrt(1-congestion)) # v in km/hour
                        if speed>0:
                            travelTime=dist/speed       # t   in hour
                        else:
                            travelTime=np.inf
                        if maxSpeed>0:
                            minTravelTime=dist/maxSpeed # t0  in hour
                        else:
                            minTravelTime=np.inf
                        delay=travelTime-minTravelTime # delta in hour
                    else:
                        speed=0
                        travelTime=np.inf
                        minTravelTime=np.inf
                        delay=np.inf
                else:
                    # based on BPR (by default)
                    minTravelTime=dist/maxSpeed    # t0  in hour
                    travelTime=minTravelTime*(1+15*congestion**4) # t in hour
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
        
    def isStronglyConnectedNetwork(self):
        C=self.mLink2WeightedAdjacency(field='Capacity') # capacity
        S=ifn.capacity2stochastic(C)               # Markov stochastic
        if ifn.isIrreducible(S):
            return "Your network is strongly connected."
        else:
            return "Your network is not strongly connected. Clean the network data either by finding the largest strongly connected component or add a cloud node and dummy links."
        
    def mLink2WeightedAdjacency(self,field='Capacity'):
        '''
        return capacity matrix (by default)
        but depending on the fieldNo, it can also return Dist,Lanes,MaxSpeed
        
        assume fields in mLink at least contain
            LinkID,Node1,Node2,Capacity,Dist,MaxSpeed,....
        
        '''
        mLink=self.dfLink
        # get unique node IDs from second and third fields of mLink
        self.nodeIds=list(np.union1d(mLink.Node1,mLink.Node2))
        n=np.prod(len(self.nodeIds))
        A=np.zeros((n,n), dtype=np.float64)
        # fill up with 1 when there is a link
        coord=zip(mLink.Node1,mLink.Node2,mLink[field])
        for item in coord:
            (node1,node2,k)=item
            r=self.nodeIds.index(node1)
            c=self.nodeIds.index(node2)
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
        folder=os.path.abspath('..')+'\\sample\\SampleError\\'
        scenario = folder + 'Scenario.scn'
        # folder=os.path.abspath('..')+'\\sample\\SimplestScenario\\'
        # scenario=folder+'Scenario2.scn'
        # scenario=folder+'BaseScenario.scn'
        folder = os.path.abspath('..') + '\\sample\\errorscenario2\\'
        scenario = folder + 'Scenario.scn'

        print('running ',scenario)
    net=IFN_Transport(scenario)
    net.runScenario()
    
    