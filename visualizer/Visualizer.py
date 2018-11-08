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
COLOR_GOAL = 255, 0, 0
COLOR_USER = 255, 240, 200
COLOR_CIRCLE = 0, 255, 0
# goal
GOAL_TWEEN_TIME = 200 # milliseconds
GOAL_HALF_THICKNESS = 5
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
# user
targetUser = 0.5
currentUser = 0.5


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

                # otherwise (in gap zone)
                else:

                    # draw pixel as specified color
                    screen.set_at((x, y), COLOR_BACKGROUND)


# =================================
# GOAL
# =================================
def draw_goal_bar(drawColor):
    "draws bar of specified color at location of currentGoal"

    # convert [0, 1] value to pixels
    targetCenterY = math.trunc(currentGoal * WIN_SIZE[1] + 0.5)

    # draw bar at pixel coordinates
    draw_horizontal_bar(targetCenterY, GOAL_HALF_THICKNESS, drawColor, striped = True)


def set_new_goal(doTween=True):
    "sets the goal to a new random value"

    global targetGoal
    global currentGoal
    global goalTweenActive
    global goalTweenTimeStart

    # set the new goal
    targetGoal = random.random()

    # if we should do the tween
    if doTween:

        # note when the change was made - for animation purposes
        goalTweenActive = True
        goalTweenTimeStart = pygame.time.get_ticks()

    else:

        # clear the old goal
        draw_goal_bar(COLOR_BACKGROUND)

        # set currentGoal directly
        currentGoal = targetGoal

        # draw new goal
        draw_goal_bar(COLOR_GOAL)


def update_goal():
    "handles updates for the goal bar"

    global currentGoal
    global goalTweenActive

    # if animation is active
    if goalTweenActive:

        # clear the old goal
        draw_goal_bar(COLOR_BACKGROUND)

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
    draw_goal_bar(COLOR_GOAL)


# =================================
# USER
# =================================
def draw_user_bar(color) -> None:
    """draws bar of specified color at location of currentUser"""

    # convert [0, 1] value to pixels
    userCenterY = math.trunc(currentUser * WIN_SIZE[1] + 0.5)

    # draw bar at pixel coordinates
    draw_horizontal_bar(userCenterY, USER_HALF_THICKNESS, color)


def update_user():
    """update function for the user object"""

    global currentUser

    # if current and target user values are not the same
    if targetUser != currentUser:

        # clear the old user
        draw_user_bar(COLOR_BACKGROUND)

        # set currentUser directly
        currentUser = targetUser

    # draw new user
    draw_user_bar(COLOR_USER)


# =================================
# GENERAL
# =================================
def start():
    "initialization Fucntion - called before first update"

    set_new_goal(doTween = False)
    draw_user_bar(COLOR_USER)


def update():
    "Update Fucntion - called once per frame"

    # update the goal
    update_goal()

    # update the user
    update_user()


def process_input() -> int:
    """Receives and processes input"""

    global targetUser
    global gamepad

    # look at all current events
    for e in pygame.event.get():

        # quit event
        if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
            return 0

        # change goal
        elif e.type == KEYDOWN and e.key == K_n:
            set_new_goal()

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

    global clock
    global screen
    global gamepad

    # general initialization
    random.seed()
    clock = pygame.time.Clock()
    pygame.init()

    # screen initialization
    screen = pygame.display.set_mode(WIN_SIZE)
    pygame.display.set_caption("Visualizer")
    screen.fill(COLOR_BACKGROUND)

    # gamepad initialization
    pygame.joystick.init()
    num_joysticks = pygame.joystick.get_count()
    if num_joysticks > 0:
        gamepad = pygame.joystick.Joystick(0)
        gamepad.init()  # now we will receive events for the gamepad

    # initialization
    start()

    # main game loop
    while True:

        # main update
        update()

        # handle input here
        if process_input() == 0:
            break

        # boilerplate
        pygame.display.update()
        clock.tick(60)


# =================================
# STARTUP
# =================================
if __name__ == '__main__':
    main()


