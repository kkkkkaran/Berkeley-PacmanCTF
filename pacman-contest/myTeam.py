# myTeam.py
# ---------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import random, time, util
from game import Directions, Actions
import game
import sys
import copy
import collections
# sys.setrecursionlimit(sys.getrecursionlimit() * 10)


###############################
# Pac-Champs- #
###############################


def createTeam(firstIndex, secondIndex, isRed,
               first='DummyAgent', second='DefenseAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.

    return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########


weights = util.Counter()
weights['nearestFoodAStar'] = -1


class DummyAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """

    # ### The below code is going to be called by the game ### #

	# **kwargs ~ alows you to pass KEYWORD argurments

    def __init__(self, *args, **kwargs):
        '''
        Initialize agent
        '''
###CC this sections is left to change 
        # Initialize all weights
        self.numGamePoint = 0
        self.weights = util.Counter()
        self.numTraining = kwargs.pop('numTraining', 0)
        self.trainingFindingPower = .5
        self.testingFindingPower = .05

        self.learningPower = .2
        self.findingPower = .8
        self.discountFactor = .99

        # Manually put in weights here
		# i think numTraining == 0  refers to an actual game, i.e. when we stop training
        if self.numTraining == 0:
            self.weights.update({'score': 0.6809099995971538,
			'numMyTeamFood': 23.6565508664964, 'opponent_0_distance': 2.0699359632136902,
			'numOpponentTeamFood': 23.633853866509785, 'bias': 115.8643705168336,
			'opponent_2_distance': 1.9917190914963816, 'nearestFoodAStar': -1.9670769570603142})

        CaptureAgent.__init__(self, *args, **kwargs)

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).

        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)

        IMPORTANT: This method may run for at most 15 seconds.
        """

        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        CaptureAgent.registerInitialState(self, gameState)
        self.numGamePoint += 1

        # Your initialization code goes here, if you need any.
        self.initialActionList = [Directions.STOP]
        self.initialOpponentFoodCount = self.getFood(gameState).count()
        self.initialMyTeamFoodCount = self.getFoodYouAreDefending(gameState).count()
        
#CC change here 
        if self.trainingMode():
            self.findingPower = self.trainingFindingPower
        else:
            self.findingPower = self.testingFindingPower

        # self.findingPower = self.trainingFindingPower if self.trainingMode() else self.testingFindingPower

        # Copy global weights to local once we stop training
        # if self.numGamePoint == self.numTraining + 1:
        #     self.weights = weights
##CC check weights
        self.weights['nearestFoodAStar'] = -1

    def chooseAction(self, gameState):
        """
        Picks among actions randomly.
        """

        # Observe the current state, and update our weights based on the current
		# state and any bonus we might get
        #

        lastStateObserved = self.getPreviousObservation()
        lastAction = self.initialActionList[-1]
        bonus = self.getBonus(gameState)
        self.updateWeights(lastStateObserved, lastAction, gameState, bonus)


		# what is the pupose of this random ???

        if random.random() < self.findingPower:
            action = random.choice(gameState.getLegalActions(self.index))
        else:
            action = self.getPolicy(gameState)

        if self.trainingMode():
            print('Features', self.getFeatures(gameState, action))
            print()
            print('Weights', self.weights)
            print()
            print()

        return action

    # ### The below code just belongs to us ### #

    def getBonus(self, gameState):
        if self.getPreviousObservation() is None:
            return 0

        bonus = 0
        lastStateObserved = self.getPreviousObservation()

        # Find out if we got a pac dot. If we did, add 10 points.
        previousFoodNum = self.getFood(lastStateObserved).count()
        currentFoodNum = self.getFood(gameState).count()

        bonus += 10 * (previousFoodNum - currentFoodNum)

        return bonus

    def updateWeights(self, gameState, action, nextState, bonus):
        """
        Updates our values. Called on chooseAction()
        """

        # Don't do anything on first iteration
        if self.getPreviousObservation() is None:
            return

        weightFactor = bonus + self.discountFactor * self.getValue(nextState) - self.getQValue(gameState, action)
        featureList = self.getFeatures(gameState, action)

		# updating the weights using gradient decent
        for eachWeightFeature in featureList:
            self.weights[eachWeightFeature] += self.learningPower * weightFactor * featureList[eachWeightFeature]

    def getQValue(self, gameState, action):
        """
        Returns the value we think the given action will give us.
        """

        featureList = self.getFeatures(gameState, action)
        sumQValue = 0
        for eachFeature in featureList:
            sumQValue += featureList[eachFeature] * self.weights[eachFeature]
        
        return sumQValue


        # return sum(featureList[feature] * self.weights[feature] for feature in featureList)

    def getValue(self, gameState):
        """
        Returns the Q value we're giving the current state.
        """
        currentQValue = []
        for eachAction in gameState.getLegalActions(self.index):
            currentQValue.append(self.getQValue(gameState, eachAction))
        
        value = max(currentQValue or [0]) 
        
        return value
        # return max([self.getQValue(gameState, action) for action in gameState.getLegalActions(self.index)] or [0])

    def getPolicy(self, gameState):
        """
        Returns the best action to take in this state.
        """
        legalActions = list(gameState.getLegalActions(self.index))
        # Shuffle to break ties randomly
        random.shuffle(legalActions)
        return max(legalActions or [None], key=lambda action: self.getQValue(gameState, action))

    def getFeatures(self, gameState, action):
        '''
        Returns a list of features.
        IMPORTANT: These should all return values between 0 and 1. For all new features, try to normalize them.
        '''

        # TODO: Incorporate "action" into these features (as right now they only take into account the state)
        # TODO: Add more features / figure out whihc features are important
        featureList = util.Counter()
        nextGameState = gameState.generateSuccessor(self.index, action)
        nextPosition = nextGameState.getAgentPosition(self.index)
        currentFood = self.getFood(gameState)
        nearestFoodAStarPath = self.aStarSearch(nextPosition, nextGameState, currentFood.asList())

        walls = gameState.getWalls()
        mazeSize = walls.width * walls.height

        featureList['numOpponentTeamFood'] = currentFood.count() / self.initialOpponentFoodCount
        featureList['numMyTeamFood'] = self.getFoodYouAreDefending(gameState).count() / self.initialMyTeamFoodCount
        featureList['bias'] = 1.0
        # featureList['score'] = self.getScore(gameState)

        # If it can't find the path, returns mazeSize/mazeSize
        if nearestFoodAStarPath is not None:
            featureList['nearestFoodAStar'] = len(nearestFoodAStarPath) / mazeSize
        else:
            featureList['nearestFoodAStar'] = mazeSize / mazeSize

        # featureList['nearestFoodAStar'] = (len(nearestFoodAStarPath) if nearestFoodAStarPath is not None else mazeSize) / mazeSize



		# Distance away from opponents
        # agentDistances = gameState.getAgentDistances() <== This is not used yet

        # for agent_num in self.getOpponents(gameState):
        #     featureList['opponent_' + str(agent_num) + '_distance'] = agentDistances[agent_num] / mazeSize

        return featureList

##CC this function can be removed
    # def getPreviousAction(self):
    #     return self.initialActionList[-1]

    def trainingMode(self):
        return self.numGamePoint <= self.numTraining

    def isGhost(self, gameState, index):
        """
        Returns true ONLY if we can see the agent and it's definitely a ghost
        """
        position = gameState.getAgentPosition(index)
        if position is None:
            return False
        return not (gameState.isOnRedTeam(index) ^ (position[0] < gameState.getWalls().width / 2))

    def isPacman(self, gameState, index):
        """
        Returns true ONLY if we can see the agent and it's definitely a pacman
        """
        position = gameState.getAgentPosition(index)
        if position is None:
            return False
        return not (gameState.isOnRedTeam(index) ^ (position[0] >= gameState.getWalls().width / 2))

    # ## A Star Search ## #

    def aStarSearch(self, startPosition, gameState, goalPositions, attackPacmen=True):
        """
        Finds the distance between the agent with the given index and its nearest goalPosition
        """

        walls = gameState.getWalls().asList()
        # actionList = gameState.get
        directionList = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        directionVectors = [Actions.directionToVector(eachAction) for eachAction in directionList]

        opponentIndices = self.getOpponents(gameState)
        # opponentLocations = [gameState.getAgentPosition(i) for i in opponentIndices if self.isGhost(gameState, i) and self.isPacman(gameState, self.index)]
        opponentLocations = []
        for i in opponentIndices:
            if self.isGhost(gameState, i) and self.isPacman(gameState, self.index):
                opponentLocations.append(gameState.getAgentPosition(i))

        if attackPacmen:
            attackablePacmen = []
            for i in opponentIndices:
                if self.isPacman(gameState, i) and self.isGhost(gameState, self.index):
                    attackablePacmen.append(gameState.getAgentPosition(i))
            # attackablePacmen = [gameState.getAgentPosition(i) for i in opponentIndices if self.isPacman(gameState, i) and self.isGhost(gameState, self.index)]
            goalPositions.extend(attackablePacmen)

        # Values are stored a 3-tuples, (Position, Path, TotalCost)

        presentPosition, presentPath, presentTotalCost = startPosition, [], 0
        # Priority queue uses the maze distance between the entered point and its closest goal position to decide which comes first
        priorityQueue = util.PriorityQueueWithFunction(lambda entry: entry[2] + (float('inf') if entry[0] in opponentLocations else 0) + (min(util.manhattanDistance(entry[0], endPosition) for endPosition in goalPositions)))

        # Keeps track of visited positions
        traversedPositions = set([presentPosition])

        while presentPosition not in goalPositions:

            possiblePositions = []
            for vector, action in zip(directionVectors, directionList):
                possiblePositions.append(((presentPosition[0] + vector[0], presentPosition[1] + vector[1]), action))

            legalPositions = []
            for position, action in possiblePositions:
                if position not in walls:
                    legalPositions.append((position, action))

            # possiblePositions = [((presentPosition[0] + vector[0], presentPosition[1] + vector[1]), action) for vector, action in zip(directionVectors, directionList)]
            # legalPositions = [(position, action) for position, action in possiblePositions if position not in walls]

            for position, action in legalPositions:
                if position not in traversedPositions:
                    traversedPositions.add(position)
                    priorityQueue.push((position, presentPath + [action], presentTotalCost + 1))

            # This shouldn't ever happen...But just in case...
            if len(priorityQueue.heap) == 0:
                return None
            else:
                presentPosition, presentPath, presentTotalCost = priorityQueue.pop()

        return presentPath

    def positionIsHome(self, position, gameWidth):
        return not (self.red ^ (position[0] < gameWidth / 2))

    def exploreDeadEndPositionOfPacDots(self, gameState):
        endingPositions = self.getFoodYouAreDefending(gameState).asList()
        walls = gameState.getWalls()
        wallPositions = walls.asList()

        # possiblePositions = [(x, y) for x in range(walls.width) for y in range(walls.height) if (x, y) not in wallPositions and self.positionIsHome((x, y), walls.width)]
        possiblePositions = []

    
        for x in range(walls.width):
            for y in range(walls.height):
                if (x, y) not in wallPositions and self.positionIsHome((x, y), walls.width):
                    possiblePositions.append((x, y))
        

        # startX = walls.width / 2 - 1 if self.red else walls.width / 2

        if self.red:
            startX = walls.width / 2 - 1
        else:
            startX = walls.width / 2

        # startingPositions = [position for position in possiblePositions if position[0] == startX]
        startingPositions = []
        for position in possiblePositions:
            if position[0] == startX:
                startingPositions.append(position)

        directionList = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        directionVectors = []
        # directionVectors = [Actions.directionToVector(eachAction) for eachAction in directionList]
        for eachAction in directionList:
            directionVectors.append(Actions.directionToVector(eachAction))

        # Change vectors from float to int
        directionVectors = [tuple(int(number) for number in eachVector) for eachVector in directionVectors]

        # Make source and sink
        source = (-1, -1)

        pathFlowNetwork = FlowNetwork()

        # Add all vertices
        for position in possiblePositions:
            pathFlowNetwork.AddVertex(position)
        pathFlowNetwork.AddVertex(source)

        # Add normal edges
        edges = EdgeDict()
        for position in possiblePositions:
            for eachVector in directionVectors:
                newPosition = (position[0] + eachVector[0], position[1] + eachVector[1])
                if newPosition in possiblePositions:
                    edges[(position, newPosition)] = 1

        # Add edges attached to source
        for position in startingPositions:
            edges[(source, position)] = float('inf')

        for edge in edges:
            pathFlowNetwork.AddEdge(edge[0], edge[1], edges[edge])

        deadEndCounter = collections.Counter()

        for dot in endingPositions:
            deadEndPath = pathFlowNetwork.FindDeadEnds(source, dot)
            if len(deadEndPath) == 1:
                deadEndCounter[deadEndPath[0]] += 1
            pathFlowNetwork.reset()

        maxDeadEnd = max(deadEndCounter, key=lambda vertex: deadEndCounter[vertex])
        return maxDeadEnd, deadEndCounter[maxDeadEnd]



# ### Implementation of Ford-Fulkerson algorithm, taken from https://github.com/bigbighd604/Python/blob/master/graph/Ford-Fulkerson.py and heavily modified
class Edge(object):
    def __init__(self, u, v, w):
        self.source = u
        self.target = v
        self.capacity = w
    
    def __hash__(self):
        return hash((self.source, self.target, self.capacity))

    def __repr__(self):
        return "%s->%s:%s" % (self.source, self.target, self.capacity)

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target


class FlowNetwork(object):
    def __init__(self):
        self.adj = {}
        self.flow = {}

    def AddVertex(self, vertex):
        self.adj[vertex] = []

    def GetEdges(self, v):
        return self.adj[v]

    def AddEdge(self, u, v, w=0):
        if u == v:
            raise ValueError("u == v")
        edge = Edge(u, v, w)
        redge = Edge(v, u, w)
        edge.redge = redge
        redge.redge = edge
        self.adj[u].append(edge)
        self.adj[v].append(redge)
        # Intialize all flows to zero
        self.flow[edge] = 0
        self.flow[redge] = 0

    def FindPath(self, source, target):

        presentVertex, presentPath, presentTotalCost = source, [], 0
        # Priority queue uses the maze distance between the entered point and its closest goal position to decide which comes first
        priorityQueue = util.PriorityQueueWithFunction(lambda entry: entry[2] + util.manhattanDistance(entry[0], target))

        traversedPositions = set()

        # Keeps track of visited positions
        while presentVertex != target:

            # possibleVertices = [(edge.target, edge) for edge in self.GetEdges(presentVertex)]
            possibleVertices = []
            for edge in self.GetEdges(presentVertex):
                possibleVertices.append((edge.target, edge))

            for vertex, edge in possibleVertices:
                residual = edge.capacity - self.flow[edge]
                if residual > 0 and not (edge, residual) in presentPath and (edge, residual) not in traversedPositions:
                    traversedPositions.add((edge, residual))
                    priorityQueue.push((vertex, presentPath + [(edge, residual)], presentTotalCost + 1))

            if priorityQueue.isEmpty():
                return None
            else:
                presentVertex, presentPath, presentTotalCost = priorityQueue.pop()

        return presentPath

    def FindDeadEnds(self, source, target):
        maxflow, leadingEdges = self.MaxFlow(source, target)
        paths = list(leadingEdges.values())

        deadEndPath = []
        for path in paths:
            for edge, residual in path:
                # Save the flows so we don't mess up the operation between path findings
                if self.FindPath(source, edge.target) is None:
                    deadEndPath.append(edge.target)
                    break
        assert len(deadEndPath) == maxflow
        return deadEndPath

    def MaxFlow(self, source, target):
        # This keeps track of paths that go to our destination
        leadingEdges = {}
        path = self.FindPath(source, target)
        while path is not None:
            leadingEdges[path[0]] = path
            flow = min(res for edge, res in path)
            for edge, res in path:
                self.flow[edge] += flow
                self.flow[edge.redge] -= flow

            path = self.FindPath(source, target)
        maxflow = sum(self.flow[edge] for edge in self.GetEdges(source))
        return maxflow, leadingEdges

    def reset(self):
        for edge in self.flow:
            self.flow[edge] = 0


class EdgeDict(dict):
    '''
    Keeps a list of undirected edges. Doesn't matter what order you add them in.
    '''
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        return dict.__getitem__(self, tuple(sorted(key)))

    def __setitem__(self, key, val):
        return dict.__setitem__(self, tuple(sorted(key)), val)

    def __contains__(self, key):
        return dict.__contains__(self, tuple(sorted(key)))

    def getAdjacentPositions(self, key):
        edgesContainingKey = [edge for edge in self if key in edge]
        adjacentPositions = [[position for position in edge if position != key][0] for edge in edgesContainingKey]
        return adjacentPositions


class DefenseAgent(DummyAgent):
    def __init__(self, *args, **kwargs):
        self.defenseMode = False
        self.GoToSpot = None
        CaptureAgent.__init__(self, *args, **kwargs)

    def registerInitialState(self, gameState):

        CaptureAgent.registerInitialState(self, gameState)
        deadEndPosition, numDots = self.exploreDeadEndPositionOfPacDots(gameState)
        if numDots >= 2:
            self.defenseMode = True
            self.GoToSpot = deadEndPosition
        else:
            self.defenseMode = False
            self.goToSpot = None

    def chooseAction(self, gameState):
        if self.defenseMode:
            pathToSpot = self.aStarSearch(gameState.getAgentPosition(self.index), gameState, [self.GoToSpot]) or [Directions.STOP]
            return pathToSpot[0]
        else:
            return CaptureAgent.chooseAction(self, gameState)

