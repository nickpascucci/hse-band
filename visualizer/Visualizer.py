import random, math, pygame
from pygame.locals import *

# =================================
# CONSTANTS
# =================================
# app
TITLE = "Visualizer"
WIN_SIZE = [640, 480]
# input
JOY_DEAD_ZONE = 0.2
JOY_AXIS_SCALE = 0.01
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
# input
gamepad = None
# goal
targetGoal = 0.0
currentGoal = 0.0
goalTweenActive = False
goalTweenTimeStart = 0.0
goalValues = []
goalTestActive = False
lastTestGoalSetTime = 0.0
# user
targetUser = 0.5
currentUser = -1.0


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


def toggle_goal_test_active():
    """toggles the active state of the goal test"""

    global goalTestActive

    # if currently active
    if goalTestActive:

        # turn off the test
        goalTestActive = False

    # otherwise (test not active)
    else:

        # create some new test values
        repopulate_goal_list()

        # attempt to activate the test (will fail if no goal values available)
        goalTestActive = try_set_new_goal(doTween=False)


def update_logic_goal():
    """handles logic updates for the goal"""

    # if goal test is active
    if goalTestActive:

        # if it's time for a goal change
        currentTime = pygame.time.get_ticks()
        elapsedTimeSinceLastGoalChange = currentTime - lastTestGoalSetTime;

        print ("elapsedTimeSinceLastGoalChange = " + str(elapsedTimeSinceLastGoalChange))
        if elapsedTimeSinceLastGoalChange > GOAL_INTERVAL_TIME:

            # try to set a new goal
            if not try_set_new_goal():

                # end test if cannot set new goal value
                toggle_goal_test_active()


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
    userCenterY = math.trunc(currentUser * WIN_SIZE[1] + 0.5)

    # draw bar at pixel coordinates
    draw_horizontal_bar(userCenterY, USER_HALF_THICKNESS, COLOR_USER)


def update_logic_user():
    """logic update function for the user object"""
    pass


def update_draw_user():
    """draw update function for the user object"""

    global currentUser

    # if current and target user values are not the same
    if targetUser != currentUser:

        # set currentUser directly
        currentUser = targetUser

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

    # general initialization
    random.seed()
    clock = pygame.time.Clock()
    pygame.init()

    # screen initialization
    pygame.display.set_caption("Visualizer")
    screen = pygame.display.set_mode(WIN_SIZE)

    # gamepad initialization
    pygame.joystick.init()
    num_joysticks = pygame.joystick.get_count()
    if num_joysticks > 0:
        gamepad = pygame.joystick.Joystick(0)
        gamepad.init()  # now we will receive events for the gamepad


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
            toggle_goal_test_active()

        # move goal to random location
        if e.type == KEYUP and e.key == K_g:
            try_set_new_goal(randomized=True)

    # if we have a gamepad
    if gamepad is not None:

        # handle input from right stick
        axis = gamepad.get_axis(3)
        if abs(axis) > JOY_DEAD_ZONE:

            sign = 1 if axis >= 0 else -1
            scaledValue = JOY_AXIS_SCALE * (abs(axis) - JOY_DEAD_ZONE)
            targetUser = min(max(targetUser + sign * scaledValue, 0), 1)

    return 1


def main():
    """This is the main loop"""

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
    main()


