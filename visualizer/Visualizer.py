import random, math, pygame
from pygame.locals import *

# CONSTANTS
# app
TITLE = "Visualizer"
WINSIZE = [640, 480]
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

# GLOBALS
# app
clock = None
screen = None
# goal
targetGoal = 0.0
currentGoal = 0.0
goalTweenActive = False
goalTweenTimeStart = 0.0
# user
targetUser = 0.5
currentUser = 0.5

mouse_pos = (0, 0)
mouse_down = False
mouse_scale = 0.0005
mouse_dead = 1
mouse_max = 100


def interpolate(a : float, b : float, t : float, p : float) -> float:
    "interpolate from a to b with parameter t and power p"

    return (b - a) * (t ** p) + a

def draw_circle(center : (float, float), radius : float, color):

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
                screen.set_at((x, y), color)

def draw_horizontal_bar(centerY, halfThickness, color, striped=False):
    "draws a horizontal bar on the screen"

    # determine bar bounds
    barMinY = max(0, centerY - halfThickness)
    barMaxY = min(WINSIZE[1]-1, centerY + halfThickness)

    # go through each pixel row that the bar will occupy
    for y in range(barMinY, barMaxY+1):
        for x in range(WINSIZE[0]):

            # if not striped
            if striped == False:

                # just draw pixel as specified color
                screen.set_at((x, y), color)

            # otherwise (if striped)
            else:

                # if we're in stripe zone
                subX = x % STRIPE_CYCLE_SIZE
                if subX < STRIPE_GAP_START or subX >= STRIPE_GAP_END:

                    # draw pixel as specified color
                    screen.set_at((x, y), color)

                # otherwise (in gap zone)
                else:

                    # draw pixel as specified color
                    screen.set_at((x, y), COLOR_BACKGROUND)

def draw_current_goal(color):
    "draws bar of specified color at location of currentGoal"

    # convert [0, 1] value to pixels
    targetCenterY = math.trunc(currentGoal * WINSIZE[1] + 0.5)

    # draw bar at pixel coordinates
    draw_horizontal_bar(targetCenterY, GOAL_HALF_THICKNESS, color, striped = True)

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
        draw_current_goal(COLOR_BACKGROUND)

        # set currentGoal directly
        currentGoal = targetGoal

        # draw new goal
        draw_current_goal(COLOR_GOAL)

def update_goal():
    "handles updates for the goal bar"

    global currentGoal
    global goalTweenActive

    # if animation is active
    if goalTweenActive:

        # clear the old goal
        draw_current_goal(COLOR_BACKGROUND)

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
    draw_current_goal(COLOR_GOAL)

def draw_current_user(color) -> None:
    "draws bar of specified color at location of currentUser"

    # convert [0, 1] value to pixels
    userCenterY = math.trunc(currentUser * WINSIZE[1] + 0.5)

    # draw bar at pixel coordinates
    draw_horizontal_bar(userCenterY, USER_HALF_THICKNESS, color)

def update_user():
    "update funciton for the user object"

    global currentUser
    global targetUser

    if mouse_down:

        draw_circle(mouse_pos, mouse_dead, COLOR_CIRCLE)
        currentMousePos = pygame.mouse.get_pos()
        yDiff = currentMousePos[1] - mouse_pos[1];
        sign = 1 if yDiff >= 0 else -1
        yDiff = abs(yDiff)
        yDiff = max(yDiff - mouse_dead, 0)
        targetUser = min(max(targetUser + sign * yDiff * mouse_scale, 0), 1)

    # if current and target user values are not the same
    if targetUser != currentUser:

        # clear the old user
        draw_current_user(COLOR_BACKGROUND)

        # set currentUser directly
        currentUser = targetUser

    # draw new user
    draw_current_user(COLOR_USER)

def start():
    "initialization Fucntion - called before first update"

    global stars
    global clock
    global screen

    # general initialization
    random.seed()
    clock = pygame.time.Clock()

    # screen initialization
    pygame.init()
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption("Visualizer")
    screen.fill(COLOR_BACKGROUND)

    # custom initializtion
    set_new_goal(doTween = False)
    draw_current_user(COLOR_USER)

def update():
    "Update Fucntion - called once per frame"

    # update the goal
    update_goal()

    # update the user
    update_user()

def process_input() -> int:
    "Receives and processes input"

    global targetUser
    global mouse_pos
    global mouse_down

    # look at all current events
    for e in pygame.event.get():

        # quit event
        if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
            return 0

        # change user location
        elif e.type == MOUSEBUTTONDOWN and e.button == 1:
            mouse_pos = e.pos
            mouse_down = True
        elif e.type == MOUSEBUTTONUP and e.button == 1:
            mouse_down = False

        elif e.type == KEYDOWN and e.key == K_UP:
            targetUser = min(targetUser + 0.01, 1.0)
        elif e.type == KEYDOWN and e.key == K_DOWN:
            targetUser = max(targetUser - 0.01, 0.0)

        # change goal
        elif e.type == KEYDOWN and e.key == K_n:
            set_new_goal()

    return 1

def main():
    "This is the main loop"

    # initialization
    start()

    #main game loop
    while True:

        # main update
        update()

        # handle input here
        if process_input() == 0:
            break

        # boilerplate
        pygame.display.update()
        clock.tick(60)


# if python says run, then we should run
if __name__ == '__main__':
    main()


