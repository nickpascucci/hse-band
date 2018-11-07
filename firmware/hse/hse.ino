// TODO Fix these values:
#define MOTOR_F 10
#define MOTOR_B 11
#define PACKET_SIZE 8

#define DEFAULT_INTENSITY 128
#define ON 1
#define OFF 0

#define INTENSITY 1
#define FREQUENCY 2

int mode = INTENSITY;
int front_state = OFF;
long last_front_state_change = 0;
int back_state = OFF;
long last_back_state_change = 0;

int front_intensity = 0;
int back_intensity = 0;

char front_buf[10];
char back_buf[10];

void setup() {
  Serial.begin(9600);
  pinMode(MOTOR_F, OUTPUT);
  pinMode(MOTOR_B, OUTPUT);
  Serial.println("I'm alive!");
}

void loop() {
  // Look for intensity commands, which look like {FFF;BBB}
  // (e.g. {124;256} to set the front to intensity 124 and 
  //  the back to intensity 256)
  while (Serial.available() > 0) {
    int in_byte = Serial.read();
    if (in_byte == '{') { // Opening brace; begin parsing commands
      Serial.println("Reading packet");
      memset(front_buf, 0, sizeof(front_buf)); // Initialize read buffers
      memset(back_buf, 0, sizeof(back_buf));
      int success = 0;

      for (int i = 0; i < PACKET_SIZE; i++) {
        while (!Serial.available()) {
          // Wait
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
          // Wait
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
        Serial.println(front_buf);
        Serial.println(back_buf);
        front_intensity = atoi(front_buf);
        back_intensity = atoi(back_buf);
        Serial.print(front_intensity);
        Serial.print(",");
        Serial.println(back_intensity);
      } else {
        Serial.print("Failed to read packet");
        continue;
      }
    } else if (in_byte == 'I') {
      mode = INTENSITY;
      Serial.print("Mode: Intensity");
    } else if (in_byte == 'F') {
      mode = FREQUENCY;
      last_front_state_change = millis();
      last_back_state_change = millis();
      front_state = OFF;
      back_state = OFF;
      Serial.print("Mode: Frequency");
    }
  }

  if (mode == INTENSITY) {
    analogWrite(MOTOR_F, front_intensity);
    analogWrite(MOTOR_B, back_intensity);
  } else { 
    if (front_state == ON) {
      analogWrite(MOTOR_F, DEFAULT_INTENSITY);
    } else {
      analogWrite(MOTOR_F, 0);
    }

    if (back_state == ON) {
      analogWrite(MOTOR_B, DEFAULT_INTENSITY);
    } else {
      analogWrite(MOTOR_F, 0);
    }

    if (last_front_state_change + front_intensity < millis()) {
      front_state = !front_state;
      last_front_state_change = millis();
    }

    if (last_back_state_change + back_intensity < millis()) {
      back_state = !back_state;
      last_back_state_change = millis();
    }
  }
}
