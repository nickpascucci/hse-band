// TODO Fix these values:
#define MOTOR_F 9
#define MOTOR_B 10
#define PACKET_SIZE 8

int front_intensity = 0;
int back_intensity = 0;
char front_buf[10];
char back_buf[10];

void setup() {
  Serial.begin(9600);
  pinMode(MOTOR_F, OUTPUT);
  pinMode(MOTOR_B, OUTPUT);
  
}

void loop() {
  // Look for intensity commands, which look like {FFF;BBB}
  // (e.g. {124;256} to set the front to intensity 124 and 
  //  the back to intensity 256)
  while (Serial.available() > 0) {
    int in_byte = Serial.read();
    if (in_byte == '{') { // Opening brace; begin parsing commands
      memset(front_buf, 0, sizeof(front_buf)); // Initialize read buffers
      memset(back_buf, 0, sizeof(back_buf));
      char* buf = front_buf;
      int success = 0;
      for (int i = 0; i < PACKET_SIZE; i++) {
        in_byte = Serial.read();
        if (in_byte == '}') { // Yay! A full packet arrived.
          success = 1;
          break;
        } else if (in_byte == ';') {
          buf = back_buf;
        } else {
          buf[i] = in_byte;
        }        
      }
      if (success) {
        front_intensity = atoi(front_buf);
        back_intensity = atoi(back_buf);
      } else {
        continue;
      }
    }
  }
  analogWrite(MOTOR_F, front_intensity);
  analogWrite(MOTOR_B, back_intensity);
}
