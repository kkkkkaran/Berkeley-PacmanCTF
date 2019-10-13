from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint
import math

#################
# Team Pac-Champs #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
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


#Base Class for Implementing Agents
class ReflexCaptureAgent(CaptureAgent):

    
    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
       
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
 

        features = self.evaluateAttackParameters(gameState, action)
        weights = self.getCostOfAttackParameter(gameState, action)
        return features * weights
 
    def evaluateAttackParameters(self, gameState, action):
 
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getCostOfAttackParameter(self, gameState, action):
 
        return {'successorScore': 1.0}

#Inheriting properties of Base Class
class OffensiveReflexAgent(ReflexCaptureAgent):
    def __init__(self, index):
        CaptureAgent.__init__(self, index)        

        # set current pacman coordinates
        self.currentCoordinates = (-5 ,-5)
        self.counter1 = 0
        
        # set attackNow = false. Will be used later depending upon the moves
        self.attackNow = False
        
        # keep a track of prev food count
        self.oldFoodList = []
        # keep a track of curent food count
        self.currentFoodList = []
        
        # flag to tell when to return
        self.shouldReturn = False
        
        # keep a track of pacman and see when it stops
        self.isStopped = []
        
        # set the capsuleeatingmode = false
        self.capsuleEatingMode = False
        self.modeTarget = None
        
        # keep a track of the food that it has already eaten
        self.eatenFood = 0
        self.initialTarget = []
        
        self.conditionStopped = 0
        self.capsuleLeft = 0
        self.endCapS = 0

    def registerInitialState(self, gameState):
        self.currentFoodSize = 9999999
        
        CaptureAgent.registerInitialState(self, gameState)
        self.initPosition = gameState.getAgentState(self.index).getPosition()
        self.initialAttackCoordinates(gameState)

    def initialAttackCoordinates(self ,gameState):
        
        #find best possible Attack Coordinates
        layoutInfo = []
        x = (gameState.data.layout.width - 2) // 2
        if not self.red:
            x +=1
        y = (gameState.data.layout.height - 2) // 2
        layoutInfo.extend((gameState.data.layout.width , gameState.data.layout.height ,x ,y))
       
        self.initialTarget = []
        print(layoutInfo)

        #make sure attackCoordinates are not walls
        for i in range(1, layoutInfo[1] - 1):
            if not gameState.hasWall(layoutInfo[2], i):
                self.initialTarget.append((layoutInfo[2], i))
        
        print(self.initialTarget) #remove
        noTargets = len(self.initialTarget)
        if(noTargets%2==0):
            noTargets = (noTargets//2) 
            print(noTargets)
            self.initialTarget = [self.initialTarget[noTargets]]
        else:
            noTargets = (noTargets-1)//2
            self.initialTarget = [self.initialTarget[noTargets]] 

    
    def evaluateAttackParameters(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action) 
        myPos = successor.getAgentState(self.index).getPosition() 
        foodList = self.getFood(successor).asList() 
        features['successorScore'] = self.getScore(successor) 

        if successor.getAgentState(self.index).isPacman:
            features['offence'] = 1
        else:
            features['offence'] = 0

        if foodList: 
            features['foodDistance'] = min([self.getMazeDistance(myPos, food) for food in foodList])

        opponentsIndices = []
       
        disToGhost = []
        opponentsIndices = self.getOpponents(successor)

        for i in range(len(opponentsIndices)):
            enemyPos = opponentsIndices[i]
            enmy = successor.getAgentState(enemyPos)
            if not enmy.isPacman and enmy.getPosition() != None:
                ghostPos = enmy.getPosition()
                disToGhost.append(self.getMazeDistance(myPos ,ghostPos))


        if len(disToGhost) > 0:
            minDisToGhost = min(disToGhost)
            if minDisToGhost < 5:
                features['distanceToGhost'] = minDisToGhost + features['successorScore']
            else:
                features['distanceToGhost'] = 0


        return features
    

    def getCostOfAttackParameter(self, gameState, action):

        if self.attackNow:
            if self.shouldReturn is True:
                return {'offence' :3000,
                        'successorScore': 200,
                        'foodDistance': -5,
                        'distancesToGhost' :210}
            else:
                return {'offence' :0,
                        'successorScore': 200,
                        'foodDistance': -5,
                        'distancesToGhost' :210}
        else:
            successor = self.getSuccessor(gameState, action) 
            weightGhost = 210
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None]
            if len(invaders) > 0:
                if invaders[-1].scaredTimer > 0:
                    weightGhost = 0
                    
            return {'offence' :0,
                    'successorScore': 200,
                    'foodDistance': -5,
                    'distancesToGhost' :weightGhost}

    def getOpponentPositions(self, gameState):
        return [gameState.getAgentPosition(enemy) for enemy in self.getOpponents(gameState)]

    def bestPossibleAction(self ,mcsc):
        ab = mcsc.getLegalActions(self.index)
        ab.remove(Directions.STOP)

        if len(ab) == 1:
            return ab[0]
        else:
            reverseDir = Directions.REVERSE[mcsc.getAgentState(self.index).configuration.direction]
            if reverseDir in ab:
                ab.remove(reverseDir)
            return random.choice(ab)

    def monteCarloSimulation(self ,gameState ,depth):
        ss = gameState.deepCopy()
        while depth > 0:
            ss = ss.generateSuccessor(self.index ,self.bestPossibleAction(ss))
            depth -= 1
        return self.evaluate(ss ,Directions.STOP)

    def getBestPossibleAction(self,legalActions,gameState,possibleActions,distanceToTarget):
        shortestDistance = 100000000
        for i in range (0,len(legalActions)):    
            action = legalActions[i]
            nextState = gameState.generateSuccessor(self.index, action)
            nextPosition = nextState.getAgentPosition(self.index)
            distance = self.getMazeDistance(nextPosition, self.initialTarget[0])
            distanceToTarget.append(distance)
            if(distance<shortestDistance):
                shortestDistance = distance

        bestPossibleActions = [a for a, distance in zip(legalActions, distanceToTarget) if distance == shortestDistance]
        bestPossibleAction = random.choice(bestPossibleActions)
        return bestPossibleAction
        
    def chooseAction(self, gameState):

        
        self.currentCoordinates = gameState.getAgentState(self.index).getPosition()
        
        
        """ if pacman at the starting position then setConditionStopped =1 and find the next possible best move
            else if pacman is at the first target then setConditionStopped =0 and then go for food
        """ 
        if self.currentCoordinates == self.initPosition:
            self.conditionStopped = 1

        if self.currentCoordinates == self.initialTarget[0]:
            self.conditionStopped = 0
        
        
        # find the best possible next move    
        if self.conditionStopped == 1:
            legalActions = gameState.getLegalActions(self.index)
            legalActions.remove(Directions.STOP)
            possibleActions = []
            distanceToTarget = []
            
            bestAction=self.getBestPossibleAction(legalActions,gameState,possibleActions,distanceToTarget)
            
            return bestAction

        if self.conditionStopped==0:

            self.currentFoodList = self.getFood(gameState).asList()
            self.capsuleLeft = len(self.getCapsules(gameState))
            realLastCapsuleLen = self.endCapS
            realLastFoodLen = len(self.oldFoodList)

            #As soon as pacman eats food, try to return to base, so that score gets updated
            if len(self.currentFoodList) < len(self.oldFoodList):
                self.shouldReturn = True
            self.oldFoodList = self.currentFoodList
            self.endCapS = self.capsuleLeft
            print("Capsule eainself=",self.capsuleEatingMode)

            # if agent is not a pacman, there is no need to return 
            if not gameState.getAgentState(self.index).isPacman:
                self.shouldReturn = False
                
            
            
            # check if we need to attack now, if yes then try and attack
            remainingFoodList = self.getFood(gameState).asList()
            remainingFoodSize = len(remainingFoodList)
    
        
            if remainingFoodSize == self.currentFoodSize:
                self.counter1 = self.counter1 + 1
            else:
                self.currentFoodSize = remainingFoodSize
                self.counter1 = 0
            if gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition():
                self.counter1 = 0
            if self.counter1 > 20:
                self.attackNow = True
            else:
                self.attackNow = False
            
            
            actionsBase = gameState.getLegalActions(self.index)
            actionsBase.remove(Directions.STOP)

            #find the distance to nearest enemy
            distanceToEnemy = 999999
            enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
            invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
            if len(invaders) > 0:
                distanceToEnemy = min([self.getMazeDistance(self.currentCoordinates, a.getPosition()) for a in invaders])
            
            # try and eat the capsules if possible
            
            """
                conditions to eat capsules:
                1. if there is capsule left then set the capsuleEatingMode = true
                2. if there is visible enemy then set the capsuleEatingMode = false
                3. if pacman has eaten food then set the capsuleEatingMode = false
            """
            if self.capsuleLeft < realLastCapsuleLen:
                self.capsuleEatingMode = True
                self.eatenFood = 0
            if distanceToEnemy <= 5:
                self.capsuleEatingMode = False
            if (len(self.currentFoodList) < len (self.oldFoodList)):
                self.capsuleEatingMode = False

            """
                if capsuleEatingMode is true then try and eat capsule
            """
            if self.capsuleEatingMode:
                if not gameState.getAgentState(self.index).isPacman:
                    self.eatenFood = 0

                modeMinDistance = 999999

                if len(self.currentFoodList) < realLastFoodLen:
                    self.eatenFood += 1

                if len(self.currentFoodList )==0 or self.eatenFood >= 5:
                    self.modeTarget = self.initPosition
        
                else:
                    for food in self.currentFoodList:
                        distance = self.getMazeDistance(self.currentCoordinates ,food)
                        if distance < modeMinDistance:
                            modeMinDistance = distance
                            self.modeTarget = food

                legalActions = gameState.getLegalActions(self.index)
                legalActions.remove(Directions.STOP)
                possibleActions = []
                distanceToTarget = []
                
                k=0
                while k!=len(legalActions):
                    a = legalActions[k]
                    newpos = (gameState.generateSuccessor(self.index, a)).getAgentPosition(self.index)
                    possibleActions.append(a)
                    distanceToTarget.append(self.getMazeDistance(newpos, self.modeTarget))
                    k+=1
                
                minDis1 = min(distanceToTarget)
                bestActions = [a for a, dis in zip(possibleActions, distanceToTarget) if dis== minDis1]
                bestAction = random.choice(bestActions)
                return bestAction
            else:
                """
                if capsuleEatingMode is false then find the next best move
                """
                self.eatenFood = 0
                distanceToTarget = []
                for a in actionsBase:
                    nextState = gameState.generateSuccessor(self.index, a)
                    value = 0
                    for i in range(1, 24):
                        value += self.monteCarloSimulation(nextState ,20)
                    distanceToTarget.append(value)

                best = max(distanceToTarget)
                bestActions = [a for a, v in zip(actionsBase, distanceToTarget) if v == best]
                bestAction = random.choice(bestActions)
            return bestAction




class DefensiveReflexAgent(ReflexCaptureAgent):
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.aim = None
        self.previousFood = []
        self.isFoodEaten = False
        self.counter1 = 0
        self.gazeboDict = {}
        self.counter = 0


    def setDefensiveArea(self ,gameState):

        """
        Find the best possible defense area by calculating the centre of the maze.
        """    
        mazeCentreX = (gameState.data.layout.width - 2) // 2
        if not self.red:
            mazeCentreX += 1
        mazeCentreY = (gameState.data.layout.height - 2) // 2

        self.defenceRegion = []
        for i in range(1, gameState.data.layout.height - 1):
            if not gameState.hasWall(mazeCentreX, i):
                self.defenceRegion.append((mazeCentreX, i))
 
        expectedSize = mazeCentreY
        actualSize = len(self.defenceRegion)


        for i in range(len(self .defenceRegion)):
            if expectedSize > actualSize:
                break
            else:
                self.defenceRegion.remove(self.defenceRegion[0])
                self.defenceRegion.remove(self.defenceRegion[-1])
                actualSize = len(self.defenceRegion)

        for i in range(len(self.defenceRegion)):
            if len(self.defenceRegion) > 2:
                self.defenceRegion.remove(self.defenceRegion[0])
                self.defenceRegion.remove(self.defenceRegion[-1])
            else:
                break

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.setDefensiveArea(gameState)

    def getNextDefensiveMove(self ,gameState):

        agentActions = []
        actions = gameState.getLegalActions(self.index)
        """
        Remove the stop direction from the possible actions as we do not want the pacman to stop.
        """
        rev_dir = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        actions.remove(Directions.STOP)

        for i in range(0, len(actions)-1):
            if rev_dir == actions[i]:
                actions.remove(rev_dir)


        for i in range(len(actions)):
            a = actions[i]
            new_state = gameState.generateSuccessor(self.index, a)
            if not new_state.getAgentState(self.index).isPacman:
                agentActions.append(a)

        if len(agentActions) == 0:
            self.counter1 = 0
        else:
            self.counter1 = self.counter1 + 1

        if self.counter1 > 4 or self.counter1 == 0:
            agentActions.append(rev_dir)

        return agentActions

    def chooseAction(self, gameState):
        
        """
        keep a track of the time of each move. SHould not be more than 1 sec.
        """
        mypos = gameState.getAgentPosition(self.index)
        if mypos == self.aim:
            self.aim = None
        invaders = []
        nearestInvader = []
        minDistance = float("inf")

        """
        find out the position of the enemy invader 
        """
        opponentsIndices = self.getOpponents(gameState)
        i = 0
        while i != len(opponentsIndices):
            opponentIndex = opponentsIndices[i]
            oppent = gameState.getAgentState(opponentIndex)
            if oppent.isPacman and oppent.getPosition() != None:
                oppentPos = oppent.getPosition()
                invaders.append(oppentPos)
            i = i + 1

        # if there are invaders then chase the invader and try and kill it
        if len(invaders) > 0:
            for position in invaders:
                dist = self.getMazeDistance(position ,mypos)
                if dist < minDistance:
                    minDistance = dist
                    nearestInvader.append(position)
            self.aim = nearestInvader[-1]

        # if the enemy invader has eaten food, then remove it from the possible targets
        else:
            if len(self.previousFood) > 0:
                if len(self.getFoodYouAreDefending(gameState).asList()) < len(self.previousFood):
                    yummy = set(self.previousFood) - set(self.getFoodYouAreDefending(gameState).asList())
                    self.aim = yummy.pop()

        self.previousFood = self.getFoodYouAreDefending(gameState).asList()
        # if the foodLeft is less than minimum then don't worry about the defense and try and eat as much food as possible
        if self.aim == None:
            if len(self.getFoodYouAreDefending(gameState).asList()) <= 4:
                highPriorityFood = self.getFoodYouAreDefending(gameState).asList() + self.getCapsulesYouAreDefending(gameState)
                self.aim = random.choice(highPriorityFood)
            else:
                self.aim = random.choice(self.defenceRegion)
        candAct = self.getNextDefensiveMove(gameState)
        awsomeMoves = []
        fvalues = []

        i=0
        
        # find the best possible move.
        while i < len(candAct):
            a = candAct[i]
            nextState = gameState.generateSuccessor(self.index, a)
            newpos = nextState.getAgentPosition(self.index)
            awsomeMoves.append(a)
            fvalues.append(self.getMazeDistance(newpos, self.aim))
            i = i + 1


        best = min(fvalues)
        bestActions = [a for a, v in zip(awsomeMoves, fvalues) if v == best]
        bestAction = random.choice(bestActions)
        return bestAction
