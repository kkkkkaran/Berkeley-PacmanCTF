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



class ReflexCaptureAgent(CaptureAgent):
    '''
    Methods inherited from the baselineTeam.py
    '''
    
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


class OffensiveReflexAgent(ReflexCaptureAgent):
    '''
    Inheriting properties of Base Class
    '''
    def __init__(self, index):
        CaptureAgent.__init__(self, index)        
        self.presentCoordinates = (-5 ,-5)
        self.counter = 0
        self.attack = False
        self.lastFood = []
        self.presentFoodList = []
        self.shouldReturn = False
        self.capsulePower = False
        self.targetMode = None
        self.eatenFood = 0
        self.initialTarget = []
        self.hasStopped = 0
        self.capsuleLeft = 0
        self.prevCapsuleLeft = 0

    def registerInitialState(self, gameState):
        self.currentFoodSize = 9999999
        
        CaptureAgent.registerInitialState(self, gameState)
        self.initPosition = gameState.getAgentState(self.index).getPosition()
        self.initialAttackCoordinates(gameState)

    def initialAttackCoordinates(self ,gameState):
        
        layoutInfo = []
        x = (gameState.data.layout.width - 2) // 2
        if not self.red:
            x +=1
        y = (gameState.data.layout.height - 2) // 2
        layoutInfo.extend((gameState.data.layout.width , gameState.data.layout.height ,x ,y))
       
        self.initialTarget = []

        
        for i in range(1, layoutInfo[1] - 1):
            if not gameState.hasWall(layoutInfo[2], i):
                self.initialTarget.append((layoutInfo[2], i))
        
        noTargets = len(self.initialTarget)
        if(noTargets%2==0):
            noTargets = (noTargets//2) 
            self.initialTarget = [self.initialTarget[noTargets]]
        else:
            noTargets = (noTargets-1)//2
            self.initialTarget = [self.initialTarget[noTargets]] 

    
    def evaluateAttackParameters(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action) 
        position = successor.getAgentState(self.index).getPosition() 
        foodList = self.getFood(successor).asList() 
        features['successorScore'] = self.getScore(successor) 

        if successor.getAgentState(self.index).isPacman:
            features['offence'] = 1
        else:
            features['offence'] = 0

        if foodList: 
            features['foodDistance'] = min([self.getMazeDistance(position, food) for food in foodList])

        opponentsList = []
       
        disToGhost = []
        opponentsList = self.getOpponents(successor)

        for i in range(len(opponentsList)):
            enemyPos = opponentsList[i]
            enemy = successor.getAgentState(enemyPos)
            if not enemy.isPacman and enemy.getPosition() != None:
                ghostPos = enemy.getPosition()
                disToGhost.append(self.getMazeDistance(position ,ghostPos))


        if len(disToGhost) > 0:
            minDisToGhost = min(disToGhost)
            if minDisToGhost < 5:
                features['distanceToGhost'] = minDisToGhost + features['successorScore']
            else:
                features['distanceToGhost'] = 0


        return features
    
    def getCostOfAttackParameter(self, gameState, action):
        '''
        Setting the weights manually after many iterations
        '''

        if self.attack:
            if self.shouldReturn is True:
                return {'offence' :3010,
                        'successorScore': 202,
                        'foodDistance': -8,
                        'distancesToGhost' :215}
            else:
                return {'offence' :0,
                        'successorScore': 202,
                        'foodDistance': -8,
                        'distancesToGhost' :215}
        else:
            successor = self.getSuccessor(gameState, action) 
            weightGhost = 210
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None]
            if len(invaders) > 0:
                if invaders[-1].scaredTimer > 0:
                    weightGhost = 0
                    
            return {'offence' :0,
                    'successorScore': 202,
                    'foodDistance': -8,
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

    def getBestAction(self,legalActions,gameState,possibleActions,distanceToTarget):
        shortestDistance = 9999999999
        for i in range (0,len(legalActions)):    
            action = legalActions[i]
            nextState = gameState.generateSuccessor(self.index, action)
            nextPosition = nextState.getAgentPosition(self.index)
            distance = self.getMazeDistance(nextPosition, self.initialTarget[0])
            distanceToTarget.append(distance)
            if(distance<shortestDistance):
                shortestDistance = distance

        bestActionsList = [a for a, distance in zip(legalActions, distanceToTarget) if distance == shortestDistance]
        bestAction = random.choice(bestActionsList)
        return bestAction
        
    def chooseAction(self, gameState):
        self.presentCoordinates = gameState.getAgentState(self.index).getPosition()
    
        if self.presentCoordinates == self.initPosition:
            self.hasStopped = 1
        if self.presentCoordinates == self.initialTarget[0]:
            self.hasStopped = 0

        # find next possible best move 
        if self.hasStopped == 1:
            legalActions = gameState.getLegalActions(self.index)
            legalActions.remove(Directions.STOP)
            possibleActions = []
            distanceToTarget = []
            
            bestAction=self.getBestAction(legalActions,gameState,possibleActions,distanceToTarget)
            
            return bestAction

        if self.hasStopped==0:
            self.presentFoodList = self.getFood(gameState).asList()
            self.capsuleLeft = len(self.getCapsules(gameState))
            realLastCapsuleLen = self.prevCapsuleLeft
            realLastFoodLen = len(self.lastFood)

            # Set returned = 1 when pacman has secured some food and should to return back home           
            if len(self.presentFoodList) < len(self.lastFood):
                self.shouldReturn = True
            self.lastFood = self.presentFoodList
            self.prevCapsuleLeft = self.capsuleLeft

           
            if not gameState.getAgentState(self.index).isPacman:
                self.shouldReturn = False

            # checks the attack situation           
            remainingFoodList = self.getFood(gameState).asList()
            remainingFoodSize = len(remainingFoodList)
    
        
            if remainingFoodSize == self.currentFoodSize:
                self.counter = self.counter + 1
            else:
                self.currentFoodSize = remainingFoodSize
                self.counter = 0
            if gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition():
                self.counter = 0
            if self.counter > 20:
                self.attack = True
            else:
                self.attack = False
            
            
            actionsBase = gameState.getLegalActions(self.index)
            actionsBase.remove(Directions.STOP)

            # distance to closest enemy        
            distanceToEnemy = 999999
            enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
            invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
            if len(invaders) > 0:
                distanceToEnemy = min([self.getMazeDistance(self.presentCoordinates, a.getPosition()) for a in invaders])
            
            '''
            Capsule eating:
            -> If there is capsule available then capsulePower is True.
            -> If enemy Distance is less than 5 then capsulePower is False.
            -> If pacman scored a food then return to home capsulePower is False.
            '''
            if self.capsuleLeft < realLastCapsuleLen:
                self.capsulePower = True
                self.eatenFood = 0
            if distanceToEnemy <= 5:
                self.capsulePower = False
            if (len(self.presentFoodList) < len (self.lastFood)):
                self.capsulePower = False

        
            if self.capsulePower:
                if not gameState.getAgentState(self.index).isPacman:
                    self.eatenFood = 0

                modeMinDistance = 999999

                if len(self.presentFoodList) < realLastFoodLen:
                    self.eatenFood += 1

                if len(self.presentFoodList )==0 or self.eatenFood >= 5:
                    self.targetMode = self.initPosition
        
                else:
                    for food in self.presentFoodList:
                        distance = self.getMazeDistance(self.presentCoordinates ,food)
                        if distance < modeMinDistance:
                            modeMinDistance = distance
                            self.targetMode = food

                legalActions = gameState.getLegalActions(self.index)
                legalActions.remove(Directions.STOP)
                possibleActions = []
                distanceToTarget = []
                
                k=0
                while k!=len(legalActions):
                    a = legalActions[k]
                    newpos = (gameState.generateSuccessor(self.index, a)).getAgentPosition(self.index)
                    possibleActions.append(a)
                    distanceToTarget.append(self.getMazeDistance(newpos, self.targetMode))
                    k+=1
                
                minDis = min(distanceToTarget)
                bestActions = [a for a, dis in zip(possibleActions, distanceToTarget) if dis== minDis]
                bestAction = random.choice(bestActions)
                return bestAction
            else:
               
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
        self.target = None
        self.previousFood = []
        self.counter = 0

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.setPatrolPoint(gameState)

    def setPatrolPoint(self ,gameState):
        '''
        Look for center of the maze for patrolling
        '''
        x = (gameState.data.layout.width - 2) // 2
        if not self.red:
            x += 1
        self.patrolPoints = []
        for i in range(1, gameState.data.layout.height - 1):
            if not gameState.hasWall(x, i):
                self.patrolPoints.append((x, i))

        for i in range(len(self.patrolPoints)):
            if len(self.patrolPoints) > 2:
                self.patrolPoints.remove(self.patrolPoints[0])
                self.patrolPoints.remove(self.patrolPoints[-1])
            else:
                break
    

    def getNextDefensiveMove(self ,gameState):

        agentActions = []
        actions = gameState.getLegalActions(self.index)
        
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
            self.counter = 0
        else:
            self.counter = self.counter + 1
        if self.counter > 4 or self.counter == 0:
            agentActions.append(rev_dir)

        return agentActions

    def chooseAction(self, gameState):
        
        position = gameState.getAgentPosition(self.index)
        if position == self.target:
            self.target = None
        invaders = []
        nearestInvader = []
        minDistance = float("inf")


        # Look for enemy position in our home        
        opponentsPositions = self.getOpponents(gameState)
        i = 0
        while i != len(opponentsPositions):
            opponentPos = opponentsPositions[i]
            opponent = gameState.getAgentState(opponentPos)
            if opponent.isPacman and opponent.getPosition() != None:
                opponentPos = opponent.getPosition()
                invaders.append(opponentPos)
            i = i + 1

        # if enemy is found chase it and kill it
        if len(invaders) > 0:
            for oppPosition in invaders:
                dist = self.getMazeDistance(oppPosition ,position)
                if dist < minDistance:
                    minDistance = dist
                    nearestInvader.append(oppPosition)
            self.target = nearestInvader[-1]

        # if enemy has eaten some food, then remove it from targets
        else:
            if len(self.previousFood) > 0:
                if len(self.getFoodYouAreDefending(gameState).asList()) < len(self.previousFood):
                    yummy = set(self.previousFood) - set(self.getFoodYouAreDefending(gameState).asList())
                    self.target = yummy.pop()

        self.previousFood = self.getFoodYouAreDefending(gameState).asList()
        
        if self.target == None:
            if len(self.getFoodYouAreDefending(gameState).asList()) <= 4:
                highPriorityFood = self.getFoodYouAreDefending(gameState).asList() + self.getCapsulesYouAreDefending(gameState)
                self.target = random.choice(highPriorityFood)
            else:
                self.target = random.choice(self.patrolPoints)
        candAct = self.getNextDefensiveMove(gameState)
        awsomeMoves = []
        fvalues = []

        i=0
        
        # find the best move       
        while i < len(candAct):
            a = candAct[i]
            nextState = gameState.generateSuccessor(self.index, a)
            newpos = nextState.getAgentPosition(self.index)
            awsomeMoves.append(a)
            fvalues.append(self.getMazeDistance(newpos, self.target))
            i = i + 1

        best = min(fvalues)
        bestActions = [a for a, v in zip(awsomeMoves, fvalues) if v == best]
        bestAction = random.choice(bestActions)
        return bestAction