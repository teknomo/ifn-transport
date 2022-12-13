# IFN-Transport

IFN-Transport is an extension of [Ideal Flow Network (IFN)](https://github.com/teknomo/IdealFlowNetwork) for transportation networks synthesis and analysis written in Python. The online version of IFN-Transport is also available in [Revoledu](https://people.revoledu.com/kardi/tutorial/IFN/IFN-transport.html).

One appealing reason why transportation engineers should use IFN Transport is because the existing transportation models only encourage widening the road in order to solve traffic congestion. IFN provides an alternative model that enable the engineers to justify the reduction of road width in order to reduce traffic congestion. 

Imagine sharing the road width equally for vehicles and pedestrians. How are we going to justify the important of walkway? It is actually cheaper because all the utility lines (water, internet, sewerage, electricity) can be put under the walkway and it is cheaper to open the tiles of the walkway than to destroy the asphalt or concrete road. If the government will think of long-term solution, they should create the same amount of walkway width and vehicle road width. It would also make the city very beautiful. City who honor pedestrian would eventually honor themselves. This is where the IFN kicked in. Using IFN, we think in term of overall network balance solutions and therefore we can actually reduce the road width for vehicular traffic (and provide wider width for walkway) in order to reduce traffic congestion. Check this [video on YouTube](https://youtube.com/watch?v=h2YN3QYdZqk&feature=share) about the concept of Rebalancing Congestion. Note that we should use maximum congestion instead of averaging the performance.

## What is Traffic Assignment?
Almost everyone hates traffic congestion. What can we do about it? Almost everybody has some kind of ideas to solve the traffic congestion that we face every day. The problem is how to quantify our ideas such that we can evaluate which among our ideas would really work. This is where you need the tool, called traffic assignment software, to help you in modeling the road network, get the current network performance, and then create scenarios to alter the current road network on computer based on your ideas. Comparing the network performance of these scenarios would help you understand which ideas would work and which ideas would not work and which best ideas should be implemented.

Implementing your ideas directly in the actual road construction would cost a lot of time and money and the public would suffer in your experiment. Instead, you should try first all the possible ideas on computer and then you can propose to your government on your ideas. Knowing the exact amount of saving based on the propose scenario would also help you in quantifying the justification of the actual construction.

Given a road network, we would like to know what would be the flow and congestion level and network performances. Traffic assignment is a model to help us in assigning the flow and determine the congestion level on each link. Knowing the congestion level on each link, the program would also help us in finding the other link characteristics such as speed, travel time, delay and other network performances. Our goal in creating this program is to equip you with the best tools to test your creativity such that it can democratize the task to solve the traffic congestion in your own city. We are hoping that anyone (not necessarily as transportation engineer or transportation expert), equipped with these tools, can help in solving the traffic congestion quantitatively through science rather than merely based on opinions.

Many existing traffic assignment models exist but in general, most of them suffer several problems:

1. The traffic assignment software are very expensive (about $10,000 per license and you need to pay maintenance fee per year).
2. Many traffic assignment software are very complicated. The commercial demos are very nice with very lucrative animation but when it comes to solve the real world problem, you start to get a lot of doubt. You need to be a transport expert to input the data and to run the program.
3. Many traffic assignment software requires extensive data, especially Origin-Destination (OD) demand data. The data input are tremendously very expensive to gather and without those data, you are not able to model properly. If you input with any data, then garbage in garbage out.
4. The algorithm inside these commercial software are often heuristics and you treat them as black box without knowing how does it work and what are the assumptions behind the black box. 
5. They encourage road widening as the solution of traffic congestion. IFN-Transport is probably the only tool that provide the alternative way to justify road narrowing in order to balance the traffic congestion.

In contrast, IFN is open source, free to use and free to modify and free to distribute. The usage is relatively very simple, which will be explained in this user guide and it does not requires extensive data. The ideal flow network itself has strong mathematical background, based on Markov Chain and Maximum Entropy maximization whose assumptions are clearly stated. The IFN model is based on mathematical theory and not based on heuristic approach. The more data you have, it would be more accurate but at the most parsimony level, the model can be run without any data aside from the network itself. Based on the maximum entropy principle, we assume the maximum doubt when you have no data.

# References
If you would like to know more about the scientific basis of this work. The following publications are the foundations of Ideal Flow analysis.  Kindly read and cite any of the following papers in your references if you use this software.

* Teknomo, K.(2019), Ideal Flow Network in Society 5.0 in Mahdi et al, Optimization in Large Scale Problems - Industry 4.0 and Society 5.0 Applications, Springer, p. 67-69
* Teknomo, K. and Gardon, R.W. (2019) Traffic Assignment Based on Parsimonious Data: The Ideal Flow Network, 2019 IEEE Intelligent Transportation Systems Conference (ITSC), 1393-1398.
* Teknomo, K., Gardon, R. and Saloma, C. (2019), Ideal Flow Traffic Analysis: A Case Study on a Campus Road Network, Philippine Journal of Science 148 (1): 5162.
* Teknomo, K. (2018) Ideal Flow of Markov Chain, Discrete Mathematics, Algorithms and Applications, doi: 10.1142/S1793830918500738
* Teknomo, K. and Gardon, R.W. (2017) Intersection Analysis Using the Ideal Flow Model, Proceeding of the IEEE 20th International Conference on Intelligent Transportation Systems, Oct 16-19, 2017, Yokohama, Japan
* Teknomo, K. (2017) Ideal Relative Flow Distribution on Directed Network, Proceeding of the 12th Eastern Asia Society for Transportation Studies (EASTS), Ho Chi Minh, Vietnam Sept 18-21, 2017.
* Teknomo, K. (2017) Premagic and Ideal Flow Matrices. https://arxiv.org/abs/1706.08856
* Gardon, R.W. and Teknomo, K. (2017) Analysis of the Distribution of Traffic Density Using the Ideal Flow Method and the Principle of Maximum Entropy, Proceedings of the 17th Philippine Computing Science Congress, Cebu City, March 2017
* Teknomo, K. (2015) Ideal Flow Based on Random Walk on Directed Graph, The 9th International collaboration Symposium on Information, Production and Systems (ISIPS 2015) 16-18 Nov 2015, Waseda University, KitaKyushu, Japan.


# Installation
There is no need for installation. [Download the zip file](https://github.com/teknomo/ifn-transport/archive/refs/heads/main.zip) and unzip the whole code into a local folder. You need to install the latest [Python 3.x](https://www.python.org/downloads/) in order to run this software.

# Run the IFN-Transport
Run **main.py** in Python.
Alternatively, go into the folder where you unzip the code of IFN Transport and change directory into that folder in Command Line and type:
> python main.py

# IFN-Transport Tutorial
The graphical user interface of the main program 
<img src="figs/main.jpg">

## Download OSM Data
Select the "Download OSM Data" button from the main.py to get the OSM2IFN.py windows, which graphical user interface is as follow.
<img src="figs/osm2ifn.jpg">

If you type the city name and press "Get Boundary" button, it might help you to fill the coordinate boundary.
Alternatively, you can "Go to OSM" web page to set the coordinate boundary
<img src="figs/osmExport.jpg">

Once the Top, Left, Right and Bottom coordinates are set, select the road type that you want to download, specify the file names of node and link if necessary. Them click "Download Map" button to download the map.

The original file from OSM is in XML format.
<img src="figs/OSMXML.jpg">

The IFN-Transport would convert it into CSV format that you can open in Excel.
<img src="figs/LinkFileExcel.jpg">

The field of capacity, distance, max speed, number of lanes, road width would be approximated if not exist in OSM. Here are the fields of the converted OSM data.

> LinkID,Node1,Node2,Capacity,Distance,MaxSpeed,NumLane,RoadWidth,RoadType,RoadName

The field of the node file from OSM data would be as follow.
> NodeID,X,Y,osmID


The data would also be cleaned automatically to get the largest strongly connected network when you check the data cleaning scheme.

Once you have downloaded the map data, click "Display Network"
<img src="figs/Fig1.jpg">

The network display can be zoomed, panned to get clearer view of the network.
<img src="figs/Fig1-zoomIn1.jpg">
<img src="figs/Fig1-zoomIn2.jpg">


## Defining Scenario
You can open the scenario window from the main.py by clicking "Define and Run IFN Scenario" button , or from OSM2IFN window by clicking "Define Scenario" button.

First, select the project folder by browsing into the project folder that you have prepared. If there are already available scenarios in the project folder, they would be listed in the dropdown for existing scenario that you can select. Otherwise, simply type the scenario name to create a new scenario.
<img src="figs/guiScenario1.jpg">

To define a scenario, you need to specify the following:
1. Scenario file name (must end with .scn)
2. Link file name 
3. Node file name
4. Travel Time model (eiter BPR or Greenshield)
5. Calibration Constraint and its value.

The link file and node file has been created when you download map from OSM. The minimum fields for link file consists of the following field:
> LinkID,Node1,Node2,Capacity,Distance,MaxSpeed

You need to modify such that the capacity is in PCU/hour, distance is in km/hour and max speed is in km/hour.

You can check the content of the link file by click "Show" button next to link file.
<img src="figs/LinkTable.jpg">

The capacity is in passenger car unit per hour (pcu/hour), the distance is in kilo meter and the max speed is in km/hour. The minimum node file would consist of the following field:

> NodeID,X,Y

Similarly, you can also check the content of the node file by click "Show" button next to node file.
<img src="figs/NodeTable.jpg">

There are there three calibration constraint:
1. Maximum Congestion level (say set to 0.9)
2. Total Flow (for instance, you set it to 14000 pcu/hour)
3. Real Flow 

## Calibration with real world flow data
When you set the calibration constraint based on real flow, you need to prepare Real-Flow file, which consist of:

> LinkID,Node1,Node2,ActualFlow

The linkID must match with the Node1,Node2 which is from the link file. Once the scenarios and the associated files are ready, save the scenario to define it. Then click "Find Scaling Factor" button to get the optimum scaling factor.

<img src="figs/guiScenario3-RealFlow.jpg">

The optimization is done by maximizing the R-square or minimizing the sum square of error (SSE).
<img src="figs/Rsquare.jpg"><img src="figs/SSE.jpg">

Set the scaling factor based on the suggested scaling factor and save the scenario. 

## Run the Scenario
Click "Run Scenario" in Scenario window to get the results. The result would be at the same name of the scenario file name but with extension of .CSV and .NET.


# Future Development
There are a lot of fun stuff to develop further and if you have any critics, comments or suggestions to improve, drop me a note. I would welcome your contribution by any means, your programming time, donation or scientific ideas and so on.

# Do your part
I hope you find this program useful for your study or work. You can help your own city by setting the base network on your city, and compute the scenarios that most likely will help to solve traffic congestion in your city. Share your ideas in social media and compare it with your friends. Talk with your city government about your ideas.
