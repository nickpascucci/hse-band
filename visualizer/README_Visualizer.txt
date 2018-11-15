Installation Instructions:
1) Download latest version of Python 3 (3.7.1 at time of this writing)
  -Link: https://www.python.org/downloads/
  -You'll want to make sure the "Add python 3.x to PATH" checkbox is selected
2) Install the 'pyserial' module
  -open command prompt
  -type: py -m pip install pyserial
3) Install the 'pygame' module
  -open command prompt
  -type: py -m pip install pygame
  
Running the game:
1) open command prompt
2) type: py [local_path]\Visualizer.py [command_line_option_1] [command_line_option_2]
  -[local_path]: the (relative or globabl) file path of the folder containing 'Visualizer.py' 
  -[command_line_option_1]: the 'name' of the subject being tested (only used for naming the data log file)
  -[command_line_option_2]: the number associated with the first test (only used for naming the data log file)
  
Controls:
  -ESC: exits the app
  -Spacebar: begins a test
  -Backspace: force ends a test
  -T: changes the test mode ('training' or 'testing')
  -M: changes the motor mode ('equal', 'opposite', or 'none')
  -S: changes the signal mode ('intensity' or 'frequency')