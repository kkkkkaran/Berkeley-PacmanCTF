# Team Pac-Champs-
# UoM COMP90054 AI Planning for Autonomy - Contest: Pacman Capture the Flag
Our final implementation is based on Monte Carlo with Heuristics Approach

# Presentation Demo
The presentation and demo link is available on youtube. 
YouTube Link:
https://www.youtube.com/watch?v=7Ib14vkOxLo

# Requirements
Python3.6 or higher

# Implementation
We have implemented two techniques.
1. Monte Carlo with Heuristics: This is our main implementation technique for the contest. The implementation is available in 'myTeam.py' file. 
2. qLearningAgent: This is our second implmentation which could not do well in the contest. The implementation is available in 'qLearningAgent.py' file.

# Execute instructions:
The pacman agent can be started as red or blue agent. Run below command:
python3 capture.py -r myTeam.py -b baselineTeam.py

We use -r option to run the agent as red. If the agent has to run as blue team use -b option which is currently used by baselineTeam in above command. 

# Layouts
The pacman game had 2 types of layouts :
1. Fixed layouts -- The above command can be used to run for fixed layouts available in layouts directory. 
2. Random layouts -- For random layouts, add -l RAND$SEED where $SEED is any random number. Command: "python3 capture.py -r myTeam.py -b baselineTeam.py -l RANDOM234" where the number 234 is the map number.

# Acknowledgement:
Pac-man implementation by UC Berkeley:
The Pac-man Projects - UC Berkeley (http://ai.berkeley.edu/project_overview.html)

# The complete detailed documentation of the algorithms used and the analysis of the algorithms can be found in the below link.**
https://gitlab.eng.unimelb.edu.au/920130/comp90054-pacman/wikis/home
