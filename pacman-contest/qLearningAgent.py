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

###############
# Pac-Champs- #
###############


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

    return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########


weights = util.Counter()
weights['nearestFoodAStar'] = -1


class DummyAgent(CaptureAgent):
    """
    Offensive agent
    """

    def __init__(self, *args, **kwargs):
        '''
        Initialize agent
        '''

        # Initialize Q values for features
        self.numGamePoint = 0
        self.weights = util.Counter()
        self.numTraining = kwargs.pop('numTraining', 0)
        self.trainingFindingPower = .5
        self.testingFindingPower = .05

        self.learningPower = .2
        self.findingPower = .8
        self.discountFactor = .99

        if self.numTraining == 0:
            self.weights.update({'score': 0.6809099995971538,
            'numMyTeamFood': 23.6565508664964, 'opponent_0_distance': 2.0699359632136902,
			'numOpponentTeamFood': 23.633853866509785, 'bias': 115.8643705168336,
			'opponent_2_distance': 1.9917190914963816, 'nearestFoodAStar': -1.9670769570603142})

        CaptureAgent.__init__(self, *args, **kwargs)

    def registerInitialState(self, gameState):
        
        '''
        Register the initial state.
        Do not delete the below line
        '''
        CaptureAgent.registerInitialState(self, gameState)
        self.numGamePoint += 1

        self.initialActionList = [Directions.STOP]
        self.initialOpponentFoodCount = self.getFood(gameState).count()
        self.initialMyTeamFoodCount = self.getFoodYouAreDefending(gameState).count()
        
        if self.trainingMode():
            self.findingPower = self.trainingFindingPower
        else:
            self.findingPower = self.testingFindingPower

        self.weights['nearestFoodAStar'] = -1

    def chooseAction(self, gameState):
        """
        Picks among actions randomly.
        Update weights or rewards from the current state
        """
        lastStateObserved = self.getPreviousObservation()
        lastAction = self.initialActionList[-1]
        bonus = self.getBonus(gameState)
        self.updateWeights(lastStateObserved, lastAction, gameState, bonus)

        if random.random() < self.findingPower:
            action = random.choice(gameState.getLegalActions(self.index))
        else:
            action = self.getBestActionToTake(gameState)

        if self.trainingMode():
            print('Features', self.getNormalizedFeaturesList(gameState, action))
            print()
            print('Weights', self.weights)
            print()
            print()

        return action

    def getBonus(self, gameState):
        if self.getPreviousObservation() is None:
            return 0

        bonus = 0
        lastStateObserved = self.getPreviousObservation()
        previousFoodNum = self.getFood(lastStateObserved).count()
        currentFoodNum = self.getFood(gameState).count()
        bonus += 10 * (previousFoodNum - currentFoodNum)

        return bonus

    def updateWeights(self, gameState, action, nextState, bonus):
        """
        Updates our values.
        No Action taken on first iteration 
        """
        if self.getPreviousObservation() is None:
            return

        weightFactor = bonus + self.discountFactor * self.getBestValue(nextState) - self.getAggregatedQValue(gameState, action)
        featureList = self.getNormalizedFeaturesList(gameState, action)

        # Updating weights
        for eachWeightFeature in featureList:
            self.weights[eachWeightFeature] += self.learningPower * weightFactor * featureList[eachWeightFeature]

    def getNormalizedFeaturesList(self, gameState, action):
        '''
        Returns a list of features.
        These should all return values between 0 and 1. For all new features, do normalize them.
        '''

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
        if nearestFoodAStarPath is not None:
            featureList['nearestFoodAStar'] = len(nearestFoodAStarPath) / mazeSize
        else:
            featureList['nearestFoodAStar'] = mazeSize / mazeSize

        return featureList

    def getAggregatedQValue(self, gameState, action):
        """
        Returns the value we think the given action will give us.
        """

        featureList = self.getNormalizedFeaturesList(gameState, action)
        sumQValue = 0
        for eachFeature in featureList:
            sumQValue += featureList[eachFeature] * self.weights[eachFeature]
        
        return sumQValue

    def getBestValue(self, gameState):
        """
        Returns the best Q value 
        """
        currentQValue = []
        for eachAction in gameState.getLegalActions(self.index):
            currentQValue.append(self.getAggregatedQValue(gameState, eachAction))
        
        value = max(currentQValue or [0]) 
        
        return value
        
    def getBestActionToTake(self, gameState):
        """
        Returns the best action to take in this state.
        """
        legalActions = list(gameState.getLegalActions(self.index))

        random.shuffle(legalActions)
        return max(legalActions or [None], key=lambda action: self.getAggregatedQValue(gameState, action))


    def trainingMode(self):
        return self.numGamePoint <= self.numTraining

    def ghostSpotted(self, gameState, index):
        """
        Returns true ONLY if we can see the agent and it's definitely a ghost
        """
        position = gameState.getAgentPosition(index)
        if position is None:
            return False
        return not (gameState.isOnRedTeam(index) ^ (position[0] < gameState.getWalls().width / 2))

    def pacmanSpotted(self, gameState, index):
        """
        Returns true ONLY if we can see the agent and it's definitely a pacman
        """
        position = gameState.getAgentPosition(index)
        if position is None:
            return False
        return not (gameState.isOnRedTeam(index) ^ (position[0] >= gameState.getWalls().width / 2))

    # aStart Search Heuristic Method    

    def aStarSearch(self, startPosition, gameState, goalPositions, attackPacmen=True):
        """
        Finds the distance between the agent with the given index and its nearest goalPosition
        """

        walls = gameState.getWalls().asList()
        directionList = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        directionVectors = [Actions.directionToVector(eachAction) for eachAction in directionList]

        opponentIndices = self.getOpponents(gameState)
        opponentLocations = []
        for i in opponentIndices:
            if self.ghostSpotted(gameState, i) and self.pacmanSpotted(gameState, self.index):
                opponentLocations.append(gameState.getAgentPosition(i))

        if attackPacmen:
            attackablePacmen = []
            for i in opponentIndices:
                if self.pacmanSpotted(gameState, i) and self.ghostSpotted(gameState, self.index):
                    attackablePacmen.append(gameState.getAgentPosition(i))
            goalPositions.extend(attackablePacmen)


        presentPosition, presentPath, presentTotalCost = startPosition, [], 0
        priorityQueue = util.PriorityQueueWithFunction(lambda entry: entry[2] + (float('inf') if entry[0] in opponentLocations else 0) + (min(util.manhattanDistance(entry[0], endPosition) for endPosition in goalPositions)))

        # For tracking visited nodes
        traversedPositions = set([presentPosition])

        while presentPosition not in goalPositions:

            possiblePositions = []
            for vector, action in zip(directionVectors, directionList):
                possiblePositions.append(((presentPosition[0] + vector[0], presentPosition[1] + vector[1]), action))

            legalPositions = []
            for position, action in possiblePositions:
                if position not in walls:
                    legalPositions.append((position, action))
            for position, action in legalPositions:
                if position not in traversedPositions:
                    traversedPositions.add(position)
                    priorityQueue.push((position, presentPath + [action], presentTotalCost + 1))
            if len(priorityQueue.heap) == 0:
                return None
            else:
                presentPosition, presentPath, presentTotalCost = priorityQueue.pop()

        return presentPath

    def positionIsHome(self, position, gameWidth):
        return not (self.red ^ (position[0] < gameWidth / 2))

    def exploreDeadEndPositionOfPacDots(self, gameState):
        '''
        This method finds the dead end positions where pacman can get stuck
        '''
        
        endingPositions = self.getFoodYouAreDefending(gameState).asList()
        walls = gameState.getWalls()
        wallPositions = walls.asList()
        possiblePositions = []
    
        for x in range(walls.width):
            for y in range(walls.height):
                if (x, y) not in wallPositions and self.positionIsHome((x, y), walls.width):
                    possiblePositions.append((x, y))
        if self.red:
            startX = walls.width / 2 - 1
        else:
            startX = walls.width / 2
        startingPositions = []
        for position in possiblePositions:
            if position[0] == startX:
                startingPositions.append(position)

        directionList = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        directionVectors = []

        for eachAction in directionList:
            directionVectors.append(Actions.directionToVector(eachAction))

        directionVectors = [tuple(int(number) for number in eachVector) for eachVector in directionVectors]

        source = (-1, -1)

        pathFlowNetwork = FlowNetwork()

        for position in possiblePositions:
            pathFlowNetwork.AddVertex(position)
        pathFlowNetwork.AddVertex(source)

        edges = EdgeDict()
        for position in possiblePositions:
            for eachVector in directionVectors:
                newPosition = (position[0] + eachVector[0], position[1] + eachVector[1])
                if newPosition in possiblePositions:
                    edges[(position, newPosition)] = 1

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
        self.flow[edge] = 0
        self.flow[redge] = 0

    def FindPath(self, source, target):

        presentVertex, presentPath, presentTotalCost = source, [], 0

        #Priority Queue to use maze distance to decide shortest distance between entry position and nearest goal

        priorityQueue = util.PriorityQueueWithFunction(lambda entry: entry[2] + util.manhattanDistance(entry[0], target))

        traversedPositions = set()

        # Track the visited positions
        while presentVertex != target:
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
        maxflow, leadingEdges = self.MaxPossibleDest(source, target)
        paths = list(leadingEdges.values())

        deadEndPath = []
        for path in paths:
            for edge, residual in path:
                if self.FindPath(source, edge.target) is None:
                    deadEndPath.append(edge.target)
                    break

        return deadEndPath

    def MaxPossibleDest(self, source, target):
        #Tracks paths that can lead to our destination
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
