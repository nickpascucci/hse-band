import csv
import pygame
import random
import serial
import serial.tools.list_ports
import sys
import threading
import time
from pygame.locals import *

# =================================
# CONSTANTS
# =================================
# app
TITLE = "Visualizer"
WIN_SIZE = [640, 460]
# input
JOY_DEAD_ZONE = 0.2
JOY_AXIS_SCALE = 0.0015
# serial communication
MESSAGING_INTERVAL = 0.5  # seconds
SERIAL_THREAD_NAME = "serial_thread"
# colors
COLOR_BACKGROUND = 20, 20, 40
COLOR_GOAL_TEST_INACTIVE = 255, 0, 0
COLOR_GOAL_TEST_ACTIVE = 0, 255, 0
COLOR_USER = 255, 240, 200
COLOR_MODE_TEXT = 255, 255, 255
# testing
TEST_MODE_TRAINING = 0
TEST_MODE_EXPERIMENTAL = 1
TEST_MODE_COUNT = 2
SIGNAL_MODE_INTENSITY = 0
SIGNAL_MODE_FREQUENCY = 1
# goal
GOAL_TWEEN_TIME = 200  # milliseconds
GOAL_HALF_THICKNESS = 5
GOAL_MIN_VALUE = 0.2
GOAL_MAX_VALUE = 0.8
GOAL_INTERVAL_TIME = 1000  # milliseconds
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
# serial communication
serialObject = None
serialCommunicationThread = None
# input
gamepad = None
# testing
testMode = TEST_MODE_TRAINING
signalMode = SIGNAL_MODE_INTENSITY
# goal
targetGoal = 0.0
currentGoal = 0.0
goalTweenActive = False
goalTweenTimeStart = 0.0
goalValues = []
goalTestActive = False
loggingStartTime = 0.0
lastTestGoalSetTime = 0.0
numLogsMade = 0
# user
targetUser = 0.5
# writer
testLogDataRows = None
outputFilePrefix = "DEFAULT"


# =================================
# HELPERS
# =================================
def text_to_screen(text, x, y, size = 50, color = (200, 000, 000)):

    text = str(text)
    font = pygame.font.Font(pygame.font.get_default_font(), size)
    text = font.render(text, True, color)
    screen.blit(text, (x, y))


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
# LOGGING
# =================================
def add_frame_info_to_test_log_data():
    """adds current frame info to test log data"""

    # if we have a test log
    if goalTestActive and testLogDataRows is not None:

        # add stuff to it
        elapsedTime = pygame.time.get_ticks() - loggingStartTime
        error = targetUser - targetGoal
        testLogDataRows.append([str(elapsedTime), str(targetUser), str(targetGoal), str(error)])


def start_logging_data():
    """begins the logging process"""

    global testLogDataRows
    global loggingStartTime

    # note when logging started
    loggingStartTime = pygame.time.get_ticks()

    # create object to hold log data for this test
    testLogDataRows = [['Time', 'Current', 'Target', 'Error']]


def write_data_and_stop_logging():
    """writes data stored in testLogDataRows to file"""

    global testLogDataRows
    global numLogsMade

    with open(format("%s_%d.csv" % (outputFilePrefix, numLogsMade)), 'w', newline='') as csvfile:
        logWriter = csv.writer(csvfile)
        logWriter.writerows(testLogDataRows)

    # increment number of logs made
    numLogsMade = numLogsMade + 1

    # clear the testLog
    testLogDataRows = None


# =================================
# THREADED SERIAL COMMUNICATION
# =================================
def calculate_vibration_values():
    """calculates vibration values to pass to arduino"""

    frontValue = round(255.0 * targetUser)
    backValue = round(255.0 * (1 - targetUser))

    return (frontValue, backValue)


def format_for_serial_communication(value1: int, value2: int) -> bytearray:
    """takes two values, formats for sending to arduino over serial"""

    value1 = value1 % 256
    value2 = value2 % 256

    value1Str = str(value1)
    value2Str = str(value2)

    if value1 < 10:
        value1Str = "00" + value1Str
    elif value1 < 100:
        value1Str = "0" + value1Str

    if value2 < 10:
        value2Str = "00" + value2Str
    elif value2 < 100:
        value2Str = "0" + value2Str

    return bytearray(format('{%s;%s}' % (value1Str, value2Str)), 'ascii')


def create_serial_communication_object():
    """creates object that will be used for communicating to arduino"""

    global serialObject

    # get the arduino port
    ports = list(serial.tools.list_ports.comports())
    arduinoPort = None
    if len(ports) > 0:
        arduinoPort = ports[0].device

    # create the serial object and open the connection
    if arduinoPort is not None:
        serialObject = serial.Serial()
        serialObject.port = arduinoPort
        serialObject.baudrate = 115200


def open_serial_communication():
    """opens serial communication"""

    if serialObject is not None:
        serialObject.open()


def close_serial_communication():
    """closes serial communication"""

    if serialObject is not None:
        serialObject.close()


def open_serial_communication_thread():
    """opens thread that facilitates communication over serial port"""

    global serialCommunicationThread

    threading.Thread(name=SERIAL_THREAD_NAME, target=serial_communication_thread).start()
    threads = threading.enumerate()
    for thread in threads:
        if thread.name == SERIAL_THREAD_NAME:
            serialCommunicationThread = thread  # threading.Thread was returning None, which is dumb


def wait_for_serial_communication_thread_close():
    """waits for serial communication thread to close"""

    global serialCommunicationThread

    if serialCommunicationThread is not None:
        serialCommunicationThread.join()
        serialCommunicationThread = None


def serial_communication_thread():
    """handles threaded communication to the arduino"""

    # so long as test is still active
    while goalTestActive and serialObject is not None:

        # calculate what values to pass
        frontValue, backValue = calculate_vibration_values()

        # send the message
        toSend = format_for_serial_communication(frontValue, backValue)
        serialObject.write(toSend)

        # wait a bit
        time.sleep(MESSAGING_INTERVAL)

    # if we have a serial object
    if serialObject is not None:

        # set to 0's before exit
        toSend = format_for_serial_communication(0, 0)
        serialObject.write(toSend)


# =================================
# GOAL
# =================================
def draw_goal_bar():
    """draws bar at location of currentGoal"""

    # convert [0, 1] value to pixels
    targetCenterY = round(currentGoal * WIN_SIZE[1])

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
    global numLogsMade
    global testLogDataRows
    global loggingStartTime
    global serialCommunicationThread

    # if we're actually changing the active state
    if active != goalTestActive:

        # if setting inactive from active
        if not active:

            # turn off the test
            goalTestActive = False

            # write out the log data
            write_data_and_stop_logging()

            # wait for communication thread to close
            wait_for_serial_communication_thread_close()

        # otherwise, if setting active from inactive (and there's no comms thread going)
        elif active and serialCommunicationThread is None:

            # create some new goal values
            repopulate_goal_list()

            # attempt to set a new goal (will fail if no goal values available)
            if try_set_new_goal(doTween=False):

                # if successful, activate test
                goalTestActive = True
                start_logging_data()
                open_serial_communication_thread()


def update_logic_goal():
    """handles logic updates for the goal"""

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

    # if we're in training mode
    if testMode == TEST_MODE_TRAINING:

        # convert [0, 1] value to pixels
        userCenterY = round(targetUser * WIN_SIZE[1])

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

    # create and open the serial communication object
    create_serial_communication_object()
    open_serial_communication()


def update_logic():
    """Update function for logic - called once per frame"""

    # add data to log
    add_frame_info_to_test_log_data()

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

    # write current signal mode
    signalModeText = "Signal: "
    if signalMode == SIGNAL_MODE_INTENSITY:
        signalModeText = signalModeText + "I"
    elif signalMode == SIGNAL_MODE_FREQUENCY:
        signalModeText = signalModeText + "F"
    text_to_screen(signalModeText, WIN_SIZE[0] - 50, WIN_SIZE[1] - 15, 12, COLOR_MODE_TEXT)


def process_input() -> int:
    """Receives and processes input"""

    global targetUser
    global gamepad
    global signalMode
    global testMode

    # look at all current events
    for e in pygame.event.get():

        # quit event
        if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
            return 0

        # start test
        if e.type == KEYUP and e.key == K_SPACE:
            set_goal_test_active(True)

        # stop test
        if e.type == KEYUP and e.key == K_BACKSPACE:
            set_goal_test_active(False)

        # change to frequency mode
        if e.type == KEYUP and e.key == K_f:
            signalMode = SIGNAL_MODE_FREQUENCY
            if serialObject is not None:
                serialObject.write(bytearray('F', 'ascii'))

        # change to intensity mode
        if e.type == KEYUP and e.key == K_i:
            signalMode = SIGNAL_MODE_INTENSITY
            if serialObject is not None:
                serialObject.write(bytearray('I', 'ascii'))

        # change testing mode
        if e.type == KEYUP and e.key == K_t:
            testMode = (testMode + 1) % TEST_MODE_COUNT

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
    global numLogsMade

    # parse command line
    if len(argv) > 0:
        outputFilePrefix = argv[0]
    if len(argv) > 1:
        numLogsMade = int(argv[1])

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

    # set test inactive before exit
    set_goal_test_active(False)

    # close serial communication
    close_serial_communication()


# =================================
# STARTUP
# =================================
if __name__ == '__main__':
    main(sys.argv[1:])


