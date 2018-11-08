// TODO Fix these values:
#define MOTOR_F 10
#define MOTOR_B 11
#define PACKET_SIZE 8

#define DEFAULT_INTENSITY 128

/**
 * In intensity mode, the front and back motors are driven using a 
 * linear relationship between the PWM rate and the value given on
 * the serial port. The value 0 is "off", and 255 is the highest
 * intensity vibration.
 */
#define INTENSITY 1

/**
 * In frequency mode the values for the motors control the duration
 * between pulses at maximum intensity, with 0 being the longest 
 * duration and 255 the shortest.
 */
#define FREQUENCY 2
#define FREQ_MODE_PULSE_WIDTH 50

int mode = INTENSITY;
int front_state = LOW;
long last_front_state_change = 0;
int back_state = LOW;
long last_back_state_change = 0;

int front_value = 0;
int back_value = 0;

char front_buf[PACKET_SIZE + 1];
char back_buf[PACKET_SIZE + 1];

void setup() {
  Serial.begin(115200);
  pinMode(MOTOR_F, OUTPUT);
  pinMode(MOTOR_B, OUTPUT);
  Serial.println("I'm alive!");
}

void loop() {
  update_motors();
  read_values();
}

void read_values() {
  // Look for value commands, which look like {FFF;BBB}
  // (e.g. {124;256} to set the front to value 124 and 
  //  the back to value 256)
  while (Serial.available() > 0) {
    int in_byte = Serial.read();

     if (in_byte == 'I') {
      mode = INTENSITY;
      Serial.print("Mode: Intensity");
    } else if (in_byte == 'F') {
      mode = FREQUENCY;
      last_front_state_change = millis();
      last_back_state_change = millis();
      front_state = LOW;
      back_state = LOW;
      Serial.print("Mode: Frequency");
    } else if (in_byte == '{') {
      Serial.println("Reading packet");

      // Initialize read buffers to 0
      memset(front_buf, 0, sizeof(front_buf));
      memset(back_buf, 0, sizeof(back_buf));
      int success = 0;

      // Parse the first part of the packet
      for (int i = 0; i < PACKET_SIZE; i++) {
        while (!Serial.available()) {
          // Wait for data to become available
        }

        in_byte = Serial.read();
        Serial.print((char) in_byte);

        if (in_byte == ';') {
          Serial.println(" <- Saw separator, moving on");
          break;
        } else {
          front_buf[i] = in_byte;
        }
      }
      
      for (int i = 0; i < PACKET_SIZE; i++) {
        while (!Serial.available()) {
          // Wait for data to become available
        }
        in_byte = Serial.read();
        Serial.print((char) in_byte);

        if (in_byte == '}') { // Yay! A full packet arrived.
          success = 1;
          Serial.println(" <- Received full packet");
          break;
        } else {
          back_buf[i] = in_byte;
        }
      }
      
      if (success) {
        Serial.println("Here's what I read:");
        Serial.print("{");
        Serial.print(front_buf);
        Serial.print(";");
        Serial.print(back_buf);
        Serial.println("}");

        front_value = atoi(front_buf);
        back_value = atoi(back_buf);
      } else {
        Serial.print("Failed to read packet");
        continue;
      }
    }
  }
}

void update_motors() {
   if (mode == INTENSITY) {
    analogWrite(MOTOR_F, front_value);
    analogWrite(MOTOR_B, back_value);
  } else {
    if (last_front_state_change + delay_from_value(front_state, front_value) < millis()) {
      front_state = !front_state;
      digitalWrite(MOTOR_F, front_state);
      last_front_state_change = millis();
    }

    if (last_back_state_change + delay_from_value(back_state, back_value) < millis()) {
      back_state = !back_state;
      digitalWrite(MOTOR_B, back_state);
      last_back_state_change = millis();
    }
  }
}

/**
 * Get the delay in milliseconds that the frequency mode should 
 * wait for a given value.
 */
int delay_from_value(int state, int value) {
  if (state == HIGH) {
    return FREQ_MODE_PULSE_WIDTH;
  } else {
    return (255 - value) * 4;
  }
}
