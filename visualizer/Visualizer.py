import csv
import math
import pygame
import random
import serial
import serial.tools.list_ports
import sys
from pygame.locals import *

# =================================
# CONSTANTS
# =================================
# app
TITLE = "Visualizer"
WIN_SIZE = [640, 480]
# input
JOY_DEAD_ZONE = 0.2
JOY_AXIS_SCALE = 0.0015
# colors
COLOR_BACKGROUND = 20, 20, 40
COLOR_GOAL_TEST_INACTIVE = 255, 0, 0
COLOR_GOAL_TEST_ACTIVE = 0, 255, 0
COLOR_USER = 255, 240, 200
COLOR_CIRCLE = 0, 255, 0
# goal
GOAL_TWEEN_TIME = 200  # milliseconds
GOAL_HALF_THICKNESS = 5
GOAL_MIN_VALUE = 0.2
GOAL_MAX_VALUE = 0.8
GOAL_INTERVAL_TIME = 2000  # milliseconds
GOALS_PER_TEST = 10
GOAL_TEST_MODE_INTENSITY = 0
GOAL_TEST_MODE_FREQUENCY = 1
# user
USER_HALF_THICKNESS = 3
# other
STRIPE_GAP_START = 15
STRIPE_GAP_END = 25
STRIPE_CYCLE_SIZE = 40

# =================================
# VARS
# =================================
# app
clock = None
screen = None
# serial
serialObject = None
# input
gamepad = None
# goal
targetGoal = 0.0
currentGoal = 0.0
goalTweenActive = False
goalTweenTimeStart = 0.0
goalValues = []
goalTestActive = False
goalTestStartTime = 0.0
lastTestGoalSetTime = 0.0
goalTestMode = GOAL_TEST_MODE_INTENSITY
numTestsRun = 0
# user
targetUser = 0.5
# writer
testLogDataRows = None
outputFilePrefix = "DEFAULT"


# =================================
# HELPERS
# =================================
def interpolate(a: float, b: float, t: float, p: float) -> float:
    "interpolate from a to b with parameter t and power p"

    return (b - a) * (t ** p) + a


def draw_circle(center: (float, float), radius: float, drawColor):

    # determine bar bounds
    xMin, xMax = center[0] - radius, center[0] + radius
    yMin, yMax = center[1] - radius, center[1] + radius

    # go through each pixel row and column that the circle can occupy
    for x in range(xMin, xMax+1):
        for y in range(yMin, yMax+1):

            # if pixel is within radius
            xDist = x - center[0];
            yDist = y - center[1];
            if xDist ** 2 + yDist ** 2 <= radius ** 2:

                # draw pixel as specified color
                screen.set_at((x, y), drawColor)


def draw_horizontal_bar(centerY, halfThickness, drawColor, striped=False):
    "draws a horizontal bar on the screen"

    # determine bar bounds
    barMinY = max(0, centerY - halfThickness)
    barMaxY = min(WIN_SIZE[1] - 1, centerY + halfThickness)

    # go through each pixel row that the bar will occupy
    for y in range(barMinY, barMaxY+1):
        for x in range(WIN_SIZE[0]):

            # if not striped
            if striped == False:

                # just draw pixel as specified color
                screen.set_at((x, y), drawColor)

            # otherwise (if striped)
            else:

                # if we're in stripe zone
                subX = x % STRIPE_CYCLE_SIZE
                if subX < STRIPE_GAP_START or subX >= STRIPE_GAP_END:

                    # draw pixel as specified color
                    screen.set_at((x, y), drawColor)


# =================================
# GOAL
# =================================
def draw_goal_bar():
    """draws bar at location of currentGoal"""

    # convert [0, 1] value to pixels
    targetCenterY = math.trunc(currentGoal * WIN_SIZE[1] + 0.5)

    # draw bar at pixel coordinates
    drawColor = COLOR_GOAL_TEST_ACTIVE if goalTestActive else COLOR_GOAL_TEST_INACTIVE
    draw_horizontal_bar(targetCenterY, GOAL_HALF_THICKNESS, drawColor, striped = True)


def repopulate_goal_list():
    """creates the list of randomly generated goals"""

    global goalValues

    # clear any existing values
    goalValues.clear()

    # if we have more than one goal per testS
    if GOALS_PER_TEST > 1:

        # make list of all indices
        goalIndices = list(range(0, GOALS_PER_TEST))

        # while we still have unused indices
        goalSeparation = (GOAL_MAX_VALUE - GOAL_MIN_VALUE) / (GOALS_PER_TEST - 1)
        while len(goalIndices) > 0:

            # grab a random index
            indicesIndex = random.randrange(0, len(goalIndices))
            goalIndex = goalIndices.pop(indicesIndex)

            # append goal value corresponding to that index to list
            goalValue = GOAL_MIN_VALUE + goalIndex * goalSeparation
            goalValues.append(goalValue)

    # otherwise (only a single goal)
    else:

        # set single goal as average of min and max
        goalValues = [(GOAL_MIN_VALUE+GOAL_MAX_VALUE)/2]


def try_set_new_goal(doTween=True, randomized=False) -> bool:
    "sets the goal to a new random value"

    global targetGoal
    global currentGoal
    global goalTweenActive
    global goalTweenTimeStart
    global goalValues
    global lastTestGoalSetTime

    # set the new goal
    if randomized:

        # go with a random number if specified
        targetGoal = random.random()

    # otherwise, if we have goal values to draw from...
    elif len(goalValues) > 0:

        # do so
        targetGoal = goalValues.pop()
        lastTestGoalSetTime = pygame.time.get_ticks()

    else:

        # fail - can't set a new goal with passed arguments
        return False

    # if we should do the tween
    if doTween:

        # note when the change was made - for animation purposes
        goalTweenActive = True
        goalTweenTimeStart = pygame.time.get_ticks()

    else:

        # set currentGoal directly
        currentGoal = targetGoal

        # draw new goal
        draw_goal_bar()

    # success!
    return True


def set_goal_test_active(active: bool):
    """toggles the active state of the goal test"""

    global goalTestActive
    global numTestsRun
    global testLogDataRows
    global goalTestStartTime

    # if setting inactive
    if not active:

        # turn off the test
        goalTestActive = False

        # write out the log data
        with open(format("%s_%d.csv" % (outputFilePrefix, numTestsRun)), 'w', newline='') as csvfile:
            logWriter = csv.writer(csvfile)
            logWriter.writerows(testLogDataRows)

        # clear the testLog
        testLogDataRows = None

    # otherwise (setting active)
    else:

        # create some new goal values
        repopulate_goal_list()

        # attempt to set a new goal (will fail if no goal values available)
        if try_set_new_goal(doTween=False):

            # if successful, activate test
            goalTestActive = True
            numTestsRun = numTestsRun + 1
            goalTestStartTime = pygame.time.get_ticks()

            # create object to hold log data for this test
            testLogDataRows = [['Time', 'Current', 'Target', 'Error']]


def update_logic_goal():
    """handles logic updates for the goal"""

    # if we have a running log
    if testLogDataRows is not None:

        # add stuff to it
        elapsedTime = pygame.time.get_ticks() - goalTestStartTime
        error = targetUser - targetGoal
        testLogDataRows.append([str(elapsedTime), str(targetUser), str(targetGoal), str(error)])

    # if goal test is active
    if goalTestActive:

        # if it's time for a goal change
        currentTime = pygame.time.get_ticks()
        elapsedTimeSinceLastGoalChange = currentTime - lastTestGoalSetTime;
        if elapsedTimeSinceLastGoalChange > GOAL_INTERVAL_TIME:

            # try to set a new goal
            if not try_set_new_goal():

                # end test if cannot set new goal value
                set_goal_test_active(False)


def update_draw_goal():
    """handles draw updates for the goal"""

    global currentGoal
    global goalTweenActive

    # if animation is active
    if goalTweenActive:

        # if tween time has expired
        currentTime = pygame.time.get_ticks()
        elapsedTime = currentTime - goalTweenTimeStart
        if elapsedTime > GOAL_TWEEN_TIME:

            # set currentGoal directly
            currentGoal = targetGoal

            # note the end of the tween
            goalTweenActive = False

        # otherwise... (tween still active)
        else:

            # interpolate to new currentGoal position
            t = elapsedTime / GOAL_TWEEN_TIME
            currentGoal = interpolate(currentGoal, targetGoal, t, 2)

    # draw the new goal
    draw_goal_bar()


# =================================
# USER
# =================================
def draw_user_bar():
    """draws bar of specified color at location of currentUser"""

    # convert [0, 1] value to pixels
    userCenterY = math.trunc(targetUser * WIN_SIZE[1] + 0.5)

    # draw bar at pixel coordinates
    draw_horizontal_bar(userCenterY, USER_HALF_THICKNESS, COLOR_USER)


def update_logic_user():
    """logic update function for the user object"""
    pass


def update_draw_user():
    """draw update function for the user object"""

    # draw new user
    draw_user_bar()


# =================================
# GENERAL
# =================================
def start():
    """initialization Function - called before first update"""

    global clock
    global screen
    global gamepad
    global serialObject

    # general initialization
    random.seed()
    clock = pygame.time.Clock()
    pygame.init()
    pygame.key.set_repeat(300, 15)

    # screen initialization
    pygame.display.set_caption("Visualizer")
    screen = pygame.display.set_mode(WIN_SIZE)

    # gamepad initialization
    pygame.joystick.init()
    num_joysticks = pygame.joystick.get_count()
    if num_joysticks > 0:
        gamepad = pygame.joystick.Joystick(0)
        gamepad.init()  # now we will receive events for the gamepad

    # get the arduino port
    ports = list(serial.tools.list_ports.comports())
    arduinoPort = None
    if len(ports) > 0:
        arduinoPort = ports[0].device

    # create the serial object and open the connection
    serialObject = serial.Serial()
    serialObject.port = arduinoPort
    serialObject.baudrate = 115200
    serialObject.open()


def update_logic():
    """Update function for logic - called once per frame"""

    # update the goal
    update_logic_goal()

    # update the user
    update_logic_user()


def update_draw():
    """Update function for drawing - called once per frame"""

    # clear the screen
    screen.fill(COLOR_BACKGROUND)

    # update the goal
    update_draw_goal()

    # update the user
    update_draw_user()


def process_input() -> int:
    """Receives and processes input"""

    global targetUser
    global gamepad

    # look at all current events
    for e in pygame.event.get():

        # quit event
        if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
            return 0

        # toggle testing on/off
        if e.type == KEYUP and e.key == K_t:
            set_goal_test_active(not goalTestActive)

        # change to frequency mode
        if e.type == KEYUP and e.key == K_f:
            goalTestMode = GOAL_TEST_MODE_FREQUENCY
            if serialObject is not None:
                serialObject.write(bytearray('F', 'ascii'))

        # change to intensity mode
        if e.type == KEYUP and e.key == K_i:
            goalTestMode = GOAL_TEST_MODE_INTENSITY
            if serialObject is not None:
                serialObject.write(bytearray('I', 'ascii'))

        # change to intensity mode
        if e.type == KEYUP and e.key == K_q and serialObject is not None:
            serialObject.write(bytearray('{000;000}', 'ascii'))

        # move goal to random location
        if e.type == KEYUP and e.key == K_g:
            try_set_new_goal(randomized=True)

        # debug keyboard input
        if e.type == KEYDOWN and e.key == K_UP:
            targetUser = min(max(targetUser - 0.01, 0), 1)
        if e.type == KEYDOWN and e.key == K_DOWN:
            targetUser = min(max(targetUser + 0.01, 0), 1)

    # if we have a gamepad
    if gamepad is not None:

        # handle input from right stick
        axis = gamepad.get_axis(3)
        if abs(axis) > JOY_DEAD_ZONE:
            sign = 1 if axis >= 0 else -1
            scaledValue = clock.get_time() * JOY_AXIS_SCALE * (abs(axis) - JOY_DEAD_ZONE)
            targetUser = min(max(targetUser + sign * scaledValue, 0), 1)

    return 1


def main(argv):
    """This is the main loop"""

    global outputFilePrefix

    # parse command line
    if len(argv) > 0:
        outputFilePrefix = argv[0]

    # initialization
    start()

    # main game loop
    while True:

        # handle input here
        if process_input() == 0:
            break

        # updates
        update_logic()
        update_draw()

        # boilerplate
        pygame.display.update()
        clock.tick(60)


# =================================
# STARTUP
# =================================
if __name__ == '__main__':
    main(sys.argv[1:])


