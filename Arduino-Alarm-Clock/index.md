---
Title: "Arduino Alarm Clock"
---

# Arduino Alarm Clock

A full-featured alarm clock built with:
- 1.44″ SPI TFT display (ST7735)  
- RTC module (DS3231)  
- EEPROM-backed settings  
- Snooze and multiple alarms  
- Custom melodies (Buzzer, Star Wars, Harry Potter, Pink Panther) 
- Multiple color choices for time and date

## Code

Browse the Arduino sketch: [code/AlarmClock.ino](code/Date_Mate_code.ino)

'''cpp
#include <Wire.h>
#include <RTClib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>
#include <EEPROM.h>
#include <avr/pgmspace.h>

// ----- Note Definitions (macros only) -----
#define NOTE_B0  31
#define NOTE_C1  33
#define NOTE_CS1 35
#define NOTE_D1  37
#define NOTE_DS1 39
#define NOTE_E1  41
#define NOTE_F1  44
#define NOTE_FS1 46
#define NOTE_G1  49
#define NOTE_GS1 52
#define NOTE_A1  55
#define NOTE_AS1 58
#define NOTE_B1  62
#define NOTE_C2  65
#define NOTE_CS2 69
#define NOTE_D2  73
#define NOTE_DS2 78
#define NOTE_E2  82
#define NOTE_F2  87
#define NOTE_FS2 93
#define NOTE_G2  98
#define NOTE_GS2 104
#define NOTE_A2  110
#define NOTE_AS2 117
#define NOTE_B2  123
#define NOTE_C3  131
#define NOTE_CS3 139
#define NOTE_D3  147
#define NOTE_DS3 156
#define NOTE_E3  165
#define NOTE_F3  175
#define NOTE_FS3 185
#define NOTE_G3  196
#define NOTE_GS3 208
#define NOTE_A3  220
#define NOTE_AS3 233
#define NOTE_B3  247
#define NOTE_C4  262
#define NOTE_CS4 277
#define NOTE_D4  294
#define NOTE_DS4 311
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_FS4 370
#define NOTE_G4  392
#define NOTE_GS4 415
#define NOTE_A4  440
#define NOTE_AS4 466
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_CS5 554
#define NOTE_D5  587
#define NOTE_DS5 622
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_FS5 740
#define NOTE_G5  784
#define NOTE_GS5 831
#define NOTE_A5  880
#define NOTE_AS5 932
#define NOTE_B5  988
#define NOTE_C6  1047
#define NOTE_CS6 1109
#define NOTE_D6  1175
#define NOTE_DS6 1245
#define NOTE_E6  1319
#define NOTE_F6  1397
#define NOTE_FS6 1480
#define NOTE_G6  1568
#define NOTE_GS6 1661
#define NOTE_A6  1760
#define NOTE_AS6 1865
#define NOTE_B6  1976
#define NOTE_C7  2093
#define NOTE_CS7 2217
#define NOTE_D7  2349
#define NOTE_DS7 2489
#define NOTE_E7  2637
#define NOTE_F7  2794
#define NOTE_FS7 2960
#define NOTE_G7  3136
#define NOTE_GS7 3322
#define NOTE_A7  3520
#define NOTE_AS7 3729
#define NOTE_B7  3951
#define NOTE_C8  4186
#define NOTE_CS8 4435
#define NOTE_D8  4699
#define NOTE_DS8 4978
#define REST      0

// ----- Pin Definitions -----
#define TFT_CS     10
#define TFT_RST    8
#define TFT_DC     9
#define BUZZER_PIN 7
#define CYCLE_BUTTON_PIN 3  
#define SNOOZE_BUTTON_PIN 6  
#define ALARM_MODE_BUTTON_PIN      2
#define ACTUAL_TIME_MODE_BUTTON_PIN 4
#define COLOR_BUTTON_PIN           5   // For changing color
#define DATE_MODE_BUTTON_PIN       12

// ----- Display Dimensions -----
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 128
#define IMAGE_WIDTH 32
#define IMAGE_HEIGHT 32
#define TIME_CHAR_WIDTH 10
#define TIME_GAP 1
#define TIME_STRING_LENGTH 8
#define WAKE_X 0
#define WAKE_Y 108
#define WAKE_W 90
#define WAKE_H 20

// ----- EEPROM Magic Number -----
#define EEPROM_MAGIC 0xDEADBEEF

// ----- Snooze Threshold -----
#define SNOOZE_THRESHOLD 1500

// ----- Melody Selection Constants -----
#define MELODY_DEFAULT      0
#define MELODY_STARWARS     1
#define MELODY_HP           2  // Hedwig's Theme
#define MELODY_PINKPANTHER  3
const int NUM_MELODIES = 4;

// ----- Global Objects -----
RTC_DS3231 rtc;
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// ----- Forward Declarations -----
bool buttonPressed(int pin);
unsigned long getButtonPressDuration(int pin);
void updateDisplay(DateTime now);
void updateDateDisplay(DateTime now);
void updateDateSettingDisplay();
void displayScene(DateTime now);
void playAlarmMelody();

// ----- Global Variables for Alarm & Modes -----
int alarmHour = 7, alarmMinute = 30;
bool alarmTriggered = false, alarmActive = false, alarmEnabled = true, buzzerState = false;
unsigned long lastBeepToggle = 0;
bool inAlarmSetting = false;
int alarmSettingStage = 0, tempAlarmHour = 0, tempAlarmMinute = 0;
int alarm2Hour = 7, alarm2Minute = 30;
bool inAlarm2Setting = false;
int alarm2SettingStage = 0, tempAlarm2Hour = 0, tempAlarm2Minute = 0;
bool inTimeSetting = false;
int timeSettingStage = 0, tempTimeHour = 0, tempTimeMinute = 0;
bool inDateSetting = false;
int dateSettingStage = 0, tempDay = 0, tempMonth = 0, tempYear = 0;
bool snoozeActive = false;
unsigned long snoozeUntil = 0;
bool manualOff = false, snoozedThisMinute = false, twentyFourFormat = true;

// ----- Global Variables for Colors (stored in PROGMEM) -----
const uint16_t timeColors[] PROGMEM = { 
  ST77XX_RED, ST77XX_GREEN, ST77XX_BLUE, ST77XX_CYAN,
  ST77XX_MAGENTA, ST77XX_YELLOW, ST77XX_WHITE,
  0xF800, 0x780F, 0xFB56, 0x07FF, 0x32CD
};
const uint8_t numTimeColors = sizeof(timeColors) / sizeof(timeColors[0]);
uint8_t currentTimeColorIndex = 0;
uint16_t currentTextColor;  // Set in setup()
uint16_t lastTextColor;     // Set in setup()

const uint16_t dateColors[] PROGMEM = { 
  ST77XX_RED, ST77XX_GREEN, ST77XX_BLUE, ST77XX_CYAN,
  ST77XX_MAGENTA, ST77XX_YELLOW, ST77XX_WHITE,
  0xF800, 0x780F, 0xFB56, 0x07FF, 0x32CD
};
const uint8_t numDateColors = sizeof(dateColors) / sizeof(dateColors[0]);
uint8_t currentDateColorIndex = 0;
uint16_t currentDateColor; // Set in setup()
uint16_t lastDateColor;    // Set in setup()

const uint16_t mainBgColor = ST77XX_BLACK;

char lastDigits[9] = "        ";
char lastAMPM[4] = "   ";
int lastSceneCode = -1;

bool showTimeFormatMessage = false;
unsigned long timeFormatMessageStart = 0;
const unsigned long timeFormatMessageDuration = 5000;

int currentMelody = 0;
unsigned long melodyNoteStartTime = 0;
int melodyNoteIndex = 0;
bool showMelodyMessage = false;
unsigned long melodyMessageStart = 0;
const unsigned long melodyMessageDuration = 5000;

// ----- Star Wars Melody (stored in PROGMEM) -----
const int starWarsTempo = 108;
const int starWarsWholenote = (60000 * 4) / starWarsTempo;
const int starWarsMelody[] PROGMEM = {
  NOTE_AS4,8, NOTE_AS4,8, NOTE_AS4,8,
  NOTE_F5,2, NOTE_C6,2,
  NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F6,2, NOTE_C6,4,  
  NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F6,2, NOTE_C6,4,  
  NOTE_AS5,8, NOTE_A5,8, NOTE_AS5,8, NOTE_G5,2, NOTE_C5,8, NOTE_C5,8, NOTE_C5,8,
  NOTE_F5,2, NOTE_C6,2,
  NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F6,2, NOTE_C6,4,  
  NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F6,2, NOTE_C6,4,
  NOTE_AS5,8, NOTE_A5,8, NOTE_AS5,8, NOTE_G5,2, NOTE_C5,-8, NOTE_C5,16, 
  NOTE_D5,-4, NOTE_D5,8, NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F5,8,
  NOTE_F5,8, NOTE_G5,8, NOTE_A5,8, NOTE_G5,4, NOTE_D5,8, NOTE_E5,4, NOTE_C5,-8, NOTE_C5,16,
  NOTE_D5,-4, NOTE_D5,8, NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F5,8,
  NOTE_C6,-8, NOTE_G5,16, NOTE_G5,2, REST,8, NOTE_C5,8,
  NOTE_D5,-4, NOTE_D5,8, NOTE_AS5,8, NOTE_A5,8, NOTE_G5,8, NOTE_F5,8,
  NOTE_F5,8, NOTE_G5,8, NOTE_A5,8, NOTE_G5,4, NOTE_D5,8, NOTE_E5,4, NOTE_C6,-8, NOTE_C6,16,
  NOTE_F6,4, NOTE_DS6,8, NOTE_CS6,4, NOTE_C6,8, NOTE_AS5,4, NOTE_GS5,8, NOTE_G5,4, NOTE_F5,8,
  NOTE_C6,1
};

// ----- Pink Panther Melody (stored in PROGMEM) -----
#define PP_TEMPO 120
#define PP_WHOLENOTE ((60000 * 4) / PP_TEMPO)
const int pinkPantherMelody[] PROGMEM = {
  REST,2, REST,4, REST,8, NOTE_DS4,8, 
  NOTE_E4,-4, REST,8, NOTE_FS4,8, NOTE_G4,-4, REST,8, NOTE_DS4,8,
  NOTE_E4,-8, NOTE_FS4,8, NOTE_G4,-8, NOTE_C5,8, NOTE_B4,-8, NOTE_E4,8, NOTE_G4,-8, NOTE_B4,8,   
  NOTE_AS4,2, NOTE_A4,-16, NOTE_G4,-16, NOTE_E4,-16, NOTE_D4,-16, 
  NOTE_E4,2, REST,4, REST,8, NOTE_DS4,4,
  NOTE_E4,-4, REST,8, NOTE_FS4,8, NOTE_G4,-4, REST,8, NOTE_DS4,8,
  NOTE_E4,-8, NOTE_FS4,8, NOTE_G4,-8, NOTE_C5,8, NOTE_B4,-8, NOTE_G4,8, NOTE_B4,-8, NOTE_E5,8,
  NOTE_DS5,1,   
  NOTE_D5,2, REST,4, REST,8, NOTE_DS4,8, 
  NOTE_E4,-4, REST,8, NOTE_FS4,8, NOTE_G4,-4, REST,8, NOTE_DS4,8,
  NOTE_E4,-8, NOTE_FS4,8, NOTE_G4,-8, NOTE_C5,8, NOTE_B4,-8, NOTE_E4,8, NOTE_G4,-8, NOTE_B4,8,   
  NOTE_AS4,2, NOTE_A4,-16, NOTE_G4,-16, NOTE_E4,-16, NOTE_D4,-16, 
  NOTE_E4,-4, REST,4,
  REST,4, NOTE_E5,-8, NOTE_D5,8, NOTE_B4,-8, NOTE_A4,8, NOTE_G4,-8, NOTE_E4,-8,
  NOTE_AS4,16, NOTE_A4,-8, NOTE_AS4,16, NOTE_A4,-8, NOTE_AS4,16, NOTE_A4,-8, NOTE_AS4,16, NOTE_A4,-8,   
  NOTE_G4,-16, NOTE_E4,-16, NOTE_D4,-16, NOTE_E4,16, NOTE_E4,16, NOTE_E4,2,
};

const int PP_NOTE_COUNT = sizeof(pinkPantherMelody) / sizeof(pinkPantherMelody[0]) / 2;
int pinkPantherNotes[PP_NOTE_COUNT];
int pinkPantherDurations[PP_NOTE_COUNT];

void setupPinkPantherMelody() {
  for (int i = 0; i < PP_NOTE_COUNT; i++) {
    pinkPantherNotes[i] = pgm_read_word(&pinkPantherMelody[i * 2]);
    int divider = pgm_read_word(&pinkPantherMelody[i * 2 + 1]);
    if (divider > 0)
      pinkPantherDurations[i] = PP_WHOLENOTE / divider;
    else if (divider < 0)
      pinkPantherDurations[i] = (PP_WHOLENOTE / abs(divider)) * 1.5;
    else
      pinkPantherDurations[i] = 0;
  }
}

const int HP_TEMPO = 144;
#define HP_WHOLENOTE ((60000 * 4) / HP_TEMPO)
const int hpMelody[] PROGMEM = {
  REST,2, NOTE_D4,4,
  NOTE_G4,-4, NOTE_AS4,8, NOTE_A4,4,
  NOTE_G4,2, NOTE_D5,4,
  NOTE_C5,-2,
  NOTE_A4,-2,
  NOTE_G4,-4, NOTE_AS4,8, NOTE_A4,4,
  NOTE_F4,2, NOTE_GS4,4,
  NOTE_D4,-1,
  NOTE_D4,4,
  
  NOTE_G4,-4, NOTE_AS4,8, NOTE_A4,4,
  NOTE_G4,2, NOTE_D5,4,
  NOTE_F5,2, NOTE_E5,4,
  NOTE_DS5,2, NOTE_B4,4,
  NOTE_DS5,-4, NOTE_D5,8, NOTE_CS5,4,
  NOTE_CS4,2, NOTE_B4,4,
  NOTE_G4,-1,
  NOTE_AS4,4,
     
  NOTE_D5,2, NOTE_AS4,4,
  NOTE_D5,2, NOTE_AS4,4,
  NOTE_DS5,2, NOTE_D5,4,
  NOTE_CS5,2, NOTE_A4,4,
  NOTE_AS4,-4, NOTE_D5,8, NOTE_CS5,4,
  NOTE_CS4,2, NOTE_D4,4,
  NOTE_D5,-1,
  REST,4, NOTE_AS4,4,
  
  NOTE_D5,2, NOTE_AS4,4,
  NOTE_D5,2, NOTE_AS4,4,
  NOTE_F5,2, NOTE_E5,4,
  NOTE_DS5,2, NOTE_B4,4,
  NOTE_DS5,-4, NOTE_D5,8, NOTE_CS5,4,
  NOTE_CS4,2, NOTE_AS4,4,
  NOTE_G4,-1,
};
const int HP_NOTE_COUNT = sizeof(hpMelody) / sizeof(hpMelody[0]) / 2;
int hpNotes[HP_NOTE_COUNT];
int hpDurations[HP_NOTE_COUNT];

void setupHpMelody() {
  for (int i = 0; i < HP_NOTE_COUNT; i++) {
    hpNotes[i] = pgm_read_word(&hpMelody[i * 2]);
    int divider = pgm_read_word(&hpMelody[i * 2 + 1]);
    if (divider > 0)
      hpDurations[i] = HP_WHOLENOTE / divider;
    else if (divider < 0)
      hpDurations[i] = (HP_WHOLENOTE / abs(divider)) * 1.5;
    else
      hpDurations[i] = 0;
  }
}

// ----- EEPROM Settings Structure -----
struct Settings {
  uint32_t magic;
  int alarmHour;
  int alarmMinute;
  int alarm2Hour;
  int alarm2Minute;
  bool twentyFourFormat;
  uint8_t currentTimeColorIndex;
  uint8_t currentDateColorIndex;
};

Settings settings;

void loadSettings() {
  EEPROM.get(0, settings);
  if (settings.magic != EEPROM_MAGIC) {
    settings.magic = EEPROM_MAGIC;
    settings.alarmHour = 7;
    settings.alarmMinute = 30;
    settings.alarm2Hour = 7;
    settings.alarm2Minute = 30;
    settings.twentyFourFormat = true;
    settings.currentTimeColorIndex = 0;
    settings.currentDateColorIndex = 0;
    EEPROM.put(0, settings);
  }
  alarmHour = settings.alarmHour;
  alarmMinute = settings.alarmMinute;
  alarm2Hour = settings.alarm2Hour;
  alarm2Minute = settings.alarm2Minute;
  twentyFourFormat = settings.twentyFourFormat;
  currentTimeColorIndex = settings.currentTimeColorIndex;
  currentDateColorIndex = settings.currentDateColorIndex;
}

void saveSettings() {
  settings.alarmHour = alarmHour;
  settings.alarmMinute = alarmMinute;
  settings.alarm2Hour = alarm2Hour;
  settings.alarm2Minute = alarm2Minute;
  settings.twentyFourFormat = twentyFourFormat;
  settings.currentTimeColorIndex = currentTimeColorIndex;
  settings.currentDateColorIndex = currentDateColorIndex;
  settings.magic = EEPROM_MAGIC;
  EEPROM.put(0, settings);
}

// --- Button Helper Functions ---
bool buttonPressed(int pin) {
  if (digitalRead(pin) == LOW) {
    delay(50);
    if (digitalRead(pin) == LOW) {
      while (digitalRead(pin) == LOW) { delay(10); }
      return true;
    }
  }
  return false;
}

unsigned long getButtonPressDuration(int pin) {
  unsigned long startTime = millis();
  while (digitalRead(pin) == LOW) { delay(10); }
  return millis() - startTime;
}

// ----- Display Update Functions -----
void updateDisplay(DateTime now) {
  int hourToDisplay;
  char newAMPM[4] = "";
  if (twentyFourFormat) { 
    hourToDisplay = now.hour(); 
  } else {
    hourToDisplay = now.hour();
    bool isPM = false;
    if (hourToDisplay >= 12) { isPM = true; if (hourToDisplay > 12) hourToDisplay -= 12; }
    else if (hourToDisplay == 0) { hourToDisplay = 12; }
    sprintf(newAMPM, " %s", (isPM ? "PM" : "AM"));
  }
  
  char newDigits[9];
  sprintf(newDigits, "%02d:%02d:%02d", hourToDisplay, now.minute(), now.second());
  int effectiveCharWidth = TIME_CHAR_WIDTH + TIME_GAP;
  int totalWidth = TIME_STRING_LENGTH * effectiveCharWidth - TIME_GAP;
  int startX = (SCREEN_WIDTH - totalWidth) / 2;
  
  if (currentTextColor != lastTextColor) {
    tft.fillRect(0, 30, SCREEN_WIDTH, 30, mainBgColor);
    memset(lastDigits, ' ', 8);
    memset(lastAMPM, ' ', 3);
    lastTextColor = currentTextColor;
  }
  
  tft.setTextSize(2);
  tft.setTextColor(currentTextColor, mainBgColor);
  for (uint8_t i = 0; i < TIME_STRING_LENGTH; i++) {
    if (newDigits[i] != lastDigits[i]) {
      int x = startX + i * effectiveCharWidth;
      int y = 35;
      tft.fillRect(x, y, TIME_CHAR_WIDTH, 16, mainBgColor);
      tft.setCursor(x, y);
      tft.print(newDigits[i]);
      lastDigits[i] = newDigits[i];
    }
  }
  
  if (!twentyFourFormat) {
    tft.setTextSize(1);
    tft.setTextColor(currentTextColor, mainBgColor);
    for (uint8_t i = 0; i < 3; i++) {
      int x = startX + (TIME_STRING_LENGTH * effectiveCharWidth) + i * 6;
      int y = 35;
      if (newAMPM[i] != lastAMPM[i]) {
        tft.fillRect(x, y, 6, 8, mainBgColor);
        tft.setCursor(x, y);
        tft.print(newAMPM[i]);
        lastAMPM[i] = newAMPM[i];
      }
    }
  }
  
  if (alarmActive || snoozeActive)
    tft.fillCircle(5, 30, 2, ST77XX_RED);
  else if (alarmEnabled)
    tft.fillCircle(5, 30, 2, tft.color565(0,255,0));
  else
    tft.fillCircle(5, 30, 2, mainBgColor);
  
  static int lastWakeType = -1;
  static char lastWakeText[20] = "";
  int currentWakeType = 0;
  char currentWakeText[20] = "";
  
  if (alarmActive || snoozeActive) { 
    currentWakeType = 1; 
    strcpy(currentWakeText, ">> WAKE UP! <<"); 
  } else if (showMelodyMessage && (millis() - melodyMessageStart < melodyMessageDuration)) {
    currentWakeType = 3;
    sprintf(currentWakeText, "%s", (currentMelody == MELODY_STARWARS ? "SW" : 
                                      currentMelody == MELODY_HP ? "HP" :
                                      currentMelody == MELODY_PINKPANTHER ? "PP" : "Def"));
  } else if (showTimeFormatMessage && (millis() - timeFormatMessageStart < timeFormatMessageDuration)) {
    currentWakeType = 2;
    strcpy(currentWakeText, (twentyFourFormat ? "24-Hr" : "12-Hr"));
  } else { 
    currentWakeType = 0; 
    currentWakeText[0] = '\0'; 
  }
  
  if (currentWakeType != lastWakeType || strcmp(currentWakeText, lastWakeText) != 0) {
    tft.fillRect(WAKE_X, WAKE_Y, WAKE_W, WAKE_H, mainBgColor);
    if (currentWakeType == 1)
      tft.setTextColor(ST77XX_RED, mainBgColor);
    else if (currentWakeType == 2)
      tft.setTextColor(ST77XX_YELLOW, mainBgColor);
    else if (currentWakeType == 3)
      tft.setTextColor(ST77XX_CYAN, mainBgColor);
    tft.setCursor(WAKE_X + 5, WAKE_Y + 5);
    tft.setTextSize(1);
    tft.print(currentWakeText);
    lastWakeType = currentWakeType;
    strcpy(lastWakeText, currentWakeText);
  }
}

void updateDateDisplay(DateTime now) {
  char dateStr[11];
  sprintf(dateStr, "%02d/%02d/%04d", now.month(), now.day(), now.year());
  tft.setTextSize(1);
  tft.setTextColor(currentDateColor, mainBgColor);
  int dateX = (SCREEN_WIDTH - 73) / 2;
  tft.setCursor(dateX, 60);
  tft.print(dateStr);
  
  const char* daysOfWeek[7] = {"Sun", "M", "T", "W", "Th", "F", "Sat"};
  int dow = now.dayOfTheWeek();
  const char* newDay = daysOfWeek[dow];
  static char lastDay[4] = "";
  static uint16_t lastDayColor = 0;
  int dayX = dateX + 63, dayY = 60;
  if (strcmp(lastDay, newDay) != 0 || lastDayColor != currentDateColor) {
    tft.fillRect(dayX, dayY, 30, 8, mainBgColor);
    tft.setTextColor(currentDateColor, mainBgColor);
    tft.setCursor(dayX, dayY);
    tft.print(newDay);
    strcpy(lastDay, newDay);
    lastDayColor = currentDateColor;
  }
}

void updateDateSettingDisplay() {
  tft.fillRect(0, 70, SCREEN_WIDTH, 15, mainBgColor);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_MAGENTA, mainBgColor);
  tft.setCursor(5, 75);
  if (dateSettingStage == 0) { tft.print("Set Date Day: "); tft.print(tempDay); }
  else if (dateSettingStage == 1) { tft.print("Set Date Month: "); tft.print(tempMonth); }
  else if (dateSettingStage == 2) { tft.print("Set Date Year: "); tft.print(tempYear); }
}

void displayScene(DateTime now) {
  int hour = now.hour(), minute = now.minute(), newSceneCode;
  if (hour >= 6 && hour < 9) newSceneCode = 1;
  else if ((hour >= 9 && hour < 17) || (hour == 17 && minute < 30)) newSceneCode = 2;
  else if ((hour == 17 && minute >= 30) || (hour == 18) || (hour == 19 && minute < 30)) newSceneCode = 3;
  else newSceneCode = 4;
  if (newSceneCode == lastSceneCode) return;
  lastSceneCode = newSceneCode;
  int x = SCREEN_WIDTH - IMAGE_WIDTH, y = SCREEN_HEIGHT - IMAGE_HEIGHT;
  tft.fillRect(x, y, IMAGE_WIDTH, IMAGE_HEIGHT, mainBgColor);
  switch(newSceneCode) {
    case 1: {
      uint16_t skyColor = tft.color565(0,120,255);
      tft.fillRect(x, y, IMAGE_WIDTH, IMAGE_HEIGHT, skyColor);
      tft.fillCircle(x + IMAGE_WIDTH/2, y + IMAGE_HEIGHT - 10, 8, tft.color565(255,140,0));
      tft.drawFastHLine(x, y + IMAGE_HEIGHT - 4, IMAGE_WIDTH, ST77XX_RED);
      break;
    }
    case 2: {
      uint16_t skyColor = tft.color565(150,220,255);
      tft.fillRect(x, y, IMAGE_WIDTH, IMAGE_HEIGHT, skyColor);
      tft.fillCircle(x + IMAGE_WIDTH/2, y + IMAGE_HEIGHT/2, 10, tft.color565(255,255,0));
      break;
    }
    case 3: {
      uint16_t skyColor = tft.color565(128,128,128);
      tft.fillRect(x, y, IMAGE_WIDTH, IMAGE_HEIGHT, skyColor);
      tft.fillCircle(x + IMAGE_WIDTH/2, y + IMAGE_HEIGHT - 12, 8, tft.color565(255,140,0));
      tft.drawFastHLine(x, y + IMAGE_HEIGHT - 4, IMAGE_WIDTH, ST77XX_RED);
      break;
    }
    case 4: {
      uint16_t skyColor = tft.color565(0,0,80);
      tft.fillRect(x, y, IMAGE_WIDTH, IMAGE_HEIGHT, skyColor);
      tft.fillCircle(x + IMAGE_WIDTH/2, y + IMAGE_HEIGHT/2, 8, tft.color565(240,240,240));
      tft.fillCircle(x + IMAGE_WIDTH/2 - 3, y + IMAGE_HEIGHT/2 - 2, 2, tft.color565(180,180,180));
      tft.fillCircle(x + IMAGE_WIDTH/2 + 2, y + IMAGE_HEIGHT/2 + 1, 1, tft.color565(180,180,180));
      break;
    }
    default: break;
  }
}

// ----- playAlarmMelody() -----
void playAlarmMelody() {
  unsigned long currentMillis = millis();
  if (currentMelody == MELODY_DEFAULT) {
    if (millis() - lastBeepToggle >= 300) {
      lastBeepToggle = millis();
      buzzerState = !buzzerState;
      if (buzzerState) tone(BUZZER_PIN, 2000); else noTone(BUZZER_PIN);
    }
    return;
  }
  if (currentMelody == MELODY_STARWARS) {
    static int starWarsIndex = 0;
    static unsigned long starWarsNoteStartTime = 0;
    if (starWarsNoteStartTime == 0) {
      starWarsIndex = 0;
      starWarsNoteStartTime = currentMillis;
      int divider = pgm_read_word(&starWarsMelody[starWarsIndex + 1]);
      int noteDuration = (divider > 0) ? starWarsWholenote / divider : (starWarsWholenote / abs(divider)) * 1.5;
      tone(BUZZER_PIN, pgm_read_word(&starWarsMelody[starWarsIndex]));
    }
    int divider = pgm_read_word(&starWarsMelody[starWarsIndex + 1]);
    int noteDuration = (divider > 0) ? starWarsWholenote / divider : (starWarsWholenote / abs(divider)) * 1.5;
    if (currentMillis - starWarsNoteStartTime >= noteDuration) {
      starWarsIndex += 2;
      if (starWarsIndex >= (sizeof(starWarsMelody) / sizeof(starWarsMelody[0])))
        starWarsIndex = 0;
      starWarsNoteStartTime = currentMillis;
      tone(BUZZER_PIN, pgm_read_word(&starWarsMelody[starWarsIndex]));
    }
    return;
  }
  if (currentMelody == MELODY_HP) {
    int *notes = hpNotes, *durations = hpDurations;
    int numNotes = HP_NOTE_COUNT;
    if (melodyNoteStartTime == 0) {
      melodyNoteStartTime = currentMillis;
      melodyNoteIndex = 0;
      tone(BUZZER_PIN, notes[melodyNoteIndex]);
    }
    if (currentMillis - melodyNoteStartTime >= durations[melodyNoteIndex]) {
      melodyNoteIndex = (melodyNoteIndex + 1) % numNotes;
      melodyNoteStartTime = currentMillis;
      tone(BUZZER_PIN, notes[melodyNoteIndex]);
    }
    return;
  }
  if (currentMelody == MELODY_PINKPANTHER) {
    int *notes = pinkPantherNotes, *durations = pinkPantherDurations;
    int numNotes = PP_NOTE_COUNT;
    if (melodyNoteStartTime == 0) {
      melodyNoteStartTime = currentMillis;
      melodyNoteIndex = 0;
      tone(BUZZER_PIN, notes[melodyNoteIndex]);
    }
    if (currentMillis - melodyNoteStartTime >= durations[melodyNoteIndex]) {
      melodyNoteIndex = (melodyNoteIndex + 1) % numNotes;
      melodyNoteStartTime = currentMillis;
      tone(BUZZER_PIN, notes[melodyNoteIndex]);
    }
    return;
  }
}

void setup() {
  loadSettings();
  // Initialize current color values from PROGMEM.
  currentTextColor = pgm_read_word(&timeColors[currentTimeColorIndex]);
  lastTextColor = currentTextColor;
  currentDateColor = pgm_read_word(&dateColors[currentDateColorIndex]);
  lastDateColor = currentDateColor;
  
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(SNOOZE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ALARM_MODE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(CYCLE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ACTUAL_TIME_MODE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(DATE_MODE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(COLOR_BUTTON_PIN, INPUT_PULLUP);
  
  tft.initR(INITR_144GREENTAB);
  tft.setRotation(0);
  tft.fillRect(0, 20, SCREEN_WIDTH, SCREEN_HEIGHT - 20, mainBgColor);
  
  if (!rtc.begin()) {
    tft.setCursor(10,10);
    tft.setTextColor(ST77XX_RED);
    tft.setTextSize(1);
    tft.println("RTC ERROR");
    while(1);
  }
  
  uint16_t headerColor = tft.color565(0,0,64);
  tft.fillRect(0, 0, SCREEN_WIDTH, 20, headerColor);
  tft.setCursor(38,5);
  tft.setTextColor(ST77XX_WHITE, headerColor);
  tft.setTextSize(1);
  tft.println("Date Mate");
  
  setupHpMelody();
  setupPinkPantherMelody();
  
  updateDisplay(rtc.now());
  updateDateDisplay(rtc.now());
  displayScene(rtc.now());
}

static bool d6WasPressed = false;
static unsigned long d6PressStart = 0;

void loop() {
  DateTime now = rtc.now();
  
  // --- Handle Color Button (pin COLOR_BUTTON_PIN) ---
  // Instead of using buttonPressed(), we directly check the pin to capture duration.
  if (digitalRead(COLOR_BUTTON_PIN) == LOW) {
    unsigned long duration = getButtonPressDuration(COLOR_BUTTON_PIN);
    if (duration < 1000) {
      currentTimeColorIndex = (currentTimeColorIndex + 1) % numTimeColors;
      currentTextColor = pgm_read_word(&timeColors[currentTimeColorIndex]);
    } else {
      currentDateColorIndex = (currentDateColorIndex + 1) % numDateColors;
      currentDateColor = pgm_read_word(&dateColors[currentDateColorIndex]);
    }
    saveSettings();
    updateDisplay(now);
    updateDateDisplay(now);
    delay(250);
  }
  
  static bool d3WasPressed = false;
  if (!inAlarmSetting && !inAlarm2Setting && !inTimeSetting && !inDateSetting) {
    if (digitalRead(CYCLE_BUTTON_PIN) == LOW) {
      if (!d3WasPressed) {
        d3WasPressed = true;
        alarmEnabled = !alarmEnabled;
        if (!alarmEnabled) { alarmActive = false; noTone(BUZZER_PIN); }
        updateDisplay(now);
        delay(200);
      }
    } else { 
      d3WasPressed = false; 
    }
  }
  
  if (digitalRead(SNOOZE_BUTTON_PIN) == LOW) {
    if (!d6WasPressed) { d6WasPressed = true; d6PressStart = millis(); }
  } else {
    if (d6WasPressed) {
      unsigned long duration = millis() - d6PressStart;
      if (alarmActive || snoozeActive) {
        if (duration >= SNOOZE_THRESHOLD) { 
          alarmActive = false; 
          alarmTriggered = true; 
          snoozeActive = false; 
          noTone(BUZZER_PIN); 
          manualOff = true; 
          updateDisplay(now); 
        } else { 
          snoozeUntil = rtc.now().unixtime() + 300; 
          snoozeActive = true; 
          alarmActive = false; 
          snoozedThisMinute = true; 
          noTone(BUZZER_PIN); 
          updateDisplay(now); 
        }
      } else {
        if (duration < 1000) {
          twentyFourFormat = !twentyFourFormat;
          memset(lastDigits, ' ', sizeof(lastDigits));
          memset(lastAMPM, ' ', sizeof(lastAMPM));
          showTimeFormatMessage = true; 
          timeFormatMessageStart = millis();
          updateDisplay(now); 
          saveSettings(); 
          delay(250);
        } else {
          currentMelody = (currentMelody + 1) % NUM_MELODIES;
          showMelodyMessage = true; 
          melodyMessageStart = millis();
          updateDisplay(now); 
          delay(250);
        }
      }
      d6WasPressed = false;
    }
  }
  
  if (!((now.hour() == alarmHour && now.minute() == alarmMinute) ||
        (now.hour() == alarm2Hour && now.minute() == alarm2Minute))) {
    manualOff = false; 
    alarmTriggered = false; 
    snoozedThisMinute = false;
  }
  
  if (snoozeActive && rtc.now().unixtime() >= snoozeUntil) {
    snoozeActive = false; 
    snoozedThisMinute = false; 
    alarmTriggered = false;
    if (!manualOff) 
      alarmActive = true;
  }
  
  if (alarmEnabled && !alarmActive && !manualOff && !snoozeActive && !snoozedThisMinute &&
      ((now.hour() == alarmHour && now.minute() == alarmMinute) ||
       (now.hour() == alarm2Hour && now.minute() == alarm2Minute))) {
    alarmTriggered = true; 
    alarmActive = true;
  }
  
  if (!inAlarmSetting && !inAlarm2Setting && !inTimeSetting && !inDateSetting) {
    if (digitalRead(ALARM_MODE_BUTTON_PIN) == LOW) {
      unsigned long pressDuration = getButtonPressDuration(ALARM_MODE_BUTTON_PIN);
      if (pressDuration >= 1000) {
        inAlarm2Setting = true; 
        alarm2SettingStage = 0; 
        tempAlarm2Hour = alarm2Hour; 
        tempAlarm2Minute = alarm2Minute;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        tft.setCursor(5,75);
        tft.setTextSize(1);
        tft.setTextColor(ST77XX_YELLOW, mainBgColor);
        tft.print("A2 Hr: "); 
        tft.print(tempAlarm2Hour);
        delay(200);
      } else {
        inAlarmSetting = true; 
        alarmSettingStage = 0; 
        tempAlarmHour = alarmHour; 
        tempAlarmMinute = alarmMinute;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        tft.setCursor(5,75);
        tft.setTextSize(1);
        tft.setTextColor(ST77XX_YELLOW, mainBgColor);
        tft.print("Set Alarm Hr: "); 
        tft.print(tempAlarmHour);
        delay(200);
      }
    }
    if (buttonPressed(ACTUAL_TIME_MODE_BUTTON_PIN)) {
      inTimeSetting = true; 
      timeSettingStage = 0; 
      tempTimeHour = now.hour(); 
      tempTimeMinute = now.minute();
      tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
      tft.setCursor(5,75);
      tft.setTextSize(1);
      tft.setTextColor(ST77XX_CYAN, mainBgColor);
      tft.print("Set Time Hr: "); 
      tft.print(tempTimeHour);
      delay(200);
    }
    if (buttonPressed(DATE_MODE_BUTTON_PIN)) {
      inDateSetting = true; 
      dateSettingStage = 0; 
      tempDay = now.day(); 
      tempMonth = now.month(); 
      tempYear = now.year();
      updateDateSettingDisplay(); 
      delay(200);
    }
  }
  
  if (inAlarmSetting) {
    if (digitalRead(CYCLE_BUTTON_PIN) == LOW) {
      unsigned long dur = getButtonPressDuration(CYCLE_BUTTON_PIN);
      if (alarmSettingStage == 0) {
        if (dur >= 1000) tempAlarmHour = 0; 
        else tempAlarmHour = (tempAlarmHour + 1) % 24;
      } else {
        if (dur >= 1000) tempAlarmMinute = 0; 
        else tempAlarmMinute = (tempAlarmMinute + 1) % 60;
      }
      tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
      tft.setCursor(5,75);
      tft.setTextSize(1);
      tft.setTextColor(ST77XX_YELLOW, mainBgColor);
      if (alarmSettingStage == 0) { tft.print("Set Alarm Hr: "); tft.print(tempAlarmHour); }
      else { tft.print("Set Alarm Mn: "); tft.print(tempAlarmMinute); }
      delay(150);
    }
    if (buttonPressed(ALARM_MODE_BUTTON_PIN)) {
      if (alarmSettingStage == 0) {
        alarmSettingStage = 1;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        tft.setCursor(5,75);
        tft.setTextSize(1);
        tft.setTextColor(ST77XX_YELLOW, mainBgColor);
        tft.print("Set Alarm Mn: "); 
        tft.print(tempAlarmMinute);
      } else {
        alarmHour = tempAlarmHour; 
        alarmMinute = tempAlarmMinute;
        inAlarmSetting = false;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        saveSettings(); 
        displayScene(rtc.now());
      }
    }
  }
  
  if (inAlarm2Setting) {
    if (digitalRead(CYCLE_BUTTON_PIN) == LOW) {
      unsigned long dur = getButtonPressDuration(CYCLE_BUTTON_PIN);
      if (alarm2SettingStage == 0) {
        if (dur >= 1000) tempAlarm2Hour = 0; 
        else tempAlarm2Hour = (tempAlarm2Hour + 1) % 24;
      } else {
        if (dur >= 1000) tempAlarm2Minute = 0; 
        else tempAlarm2Minute = (tempAlarm2Minute + 1) % 60;
      }
      tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
      tft.setCursor(5,75);
      tft.setTextSize(1);
      tft.setTextColor(ST77XX_YELLOW, mainBgColor);
      if (alarm2SettingStage == 0) { tft.print("A2 Hr: "); tft.print(tempAlarm2Hour); }
      else { tft.print("A2 Mn: "); tft.print(tempAlarm2Minute); }
      delay(150);
    }
    if (buttonPressed(ALARM_MODE_BUTTON_PIN)) {
      if (alarm2SettingStage == 0) {
        alarm2SettingStage = 1;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        tft.setCursor(5,75);
        tft.setTextSize(1);
        tft.setTextColor(ST77XX_YELLOW, mainBgColor);
        tft.print("A2 Mn: "); 
        tft.print(tempAlarm2Minute);
      } else {
        alarm2Hour = tempAlarm2Hour; 
        alarm2Minute = tempAlarm2Minute;
        inAlarm2Setting = false;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        saveSettings(); 
        displayScene(rtc.now());
      }
    }
  }
  
  if (inTimeSetting) {
    if (digitalRead(CYCLE_BUTTON_PIN) == LOW) {
      unsigned long dur = getButtonPressDuration(CYCLE_BUTTON_PIN);
      if (timeSettingStage == 0) {
        if (dur >= 1000) tempTimeHour = 0; 
        else tempTimeHour = (tempTimeHour + 1) % 24;
      } else {
        if (dur >= 1000) tempTimeMinute = 0; 
        else tempTimeMinute = (tempTimeMinute + 1) % 60;
      }
      tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
      tft.setCursor(5,75);
      tft.setTextSize(1);
      tft.setTextColor(ST77XX_CYAN, mainBgColor);
      if (timeSettingStage == 0) { tft.print("Set Time Hr: "); tft.print(tempTimeHour); }
      else { tft.print("Set Time Mn: "); tft.print(tempTimeMinute); }
      delay(150);
    }
    if (buttonPressed(ACTUAL_TIME_MODE_BUTTON_PIN)) {
      if (timeSettingStage == 0) {
        timeSettingStage = 1;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        tft.setCursor(5,75);
        tft.setTextSize(1);
        tft.setTextColor(ST77XX_CYAN, mainBgColor);
        tft.print("Set Time Mn: "); 
        tft.print(tempTimeMinute);
      } else {
        DateTime current = rtc.now();
        rtc.adjust(DateTime(current.year(), current.month(), current.day(), tempTimeHour, tempTimeMinute, 0));
        inTimeSetting = false;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        displayScene(rtc.now());
      }
    }
  }
  
  if (inDateSetting) {
    if (digitalRead(CYCLE_BUTTON_PIN) == LOW) {
      unsigned long dur = getButtonPressDuration(CYCLE_BUTTON_PIN);
      if (dateSettingStage == 0) {
        if (dur >= 1000) tempDay = 1; else tempDay = (tempDay % 31) + 1;
      } else if (dateSettingStage == 1) {
        if (dur >= 1000) tempMonth = 1; else tempMonth = (tempMonth % 12) + 1;
      } else if (dateSettingStage == 2) {
        if (dur >= 1000) tempYear = 2000; else tempYear = ((tempYear - 2000 + 1) % 100) + 2000;
      }
      updateDateSettingDisplay();
      delay(150);
    }
    if (buttonPressed(DATE_MODE_BUTTON_PIN)) {
      if (dateSettingStage < 2) { dateSettingStage++; updateDateSettingDisplay(); }
      else {
        DateTime current = rtc.now();
        rtc.adjust(DateTime(tempYear, tempMonth, tempDay, current.hour(), current.minute(), current.second()));
        inDateSetting = false;
        tft.fillRect(0,70,SCREEN_WIDTH,15, mainBgColor);
        updateDateDisplay(rtc.now());
        displayScene(rtc.now());
      }
    }
  }
  
  if (!inAlarmSetting && !inAlarm2Setting && !inTimeSetting && !inDateSetting) {
    if (alarmActive) {
      if (currentMelody == MELODY_DEFAULT) {
        if (millis() - lastBeepToggle >= 300) {
          lastBeepToggle = millis();
          buzzerState = !buzzerState;
          if (buzzerState) tone(BUZZER_PIN, 2000); else noTone(BUZZER_PIN);
        }
      } else { 
        playAlarmMelody(); 
      }
      updateDisplay(now);
    } else {
      noTone(BUZZER_PIN);
      melodyNoteStartTime = 0; 
      melodyNoteIndex = 0;
      updateDisplay(now);
    }
  }
}
'''

## Schematic

Download: 
- [PDF export](schematic/Schematic.pdf)
![Schematic Layout](schematic/Schematic.png)

## PCB Layout

 Download:
- [PNG export](pcb/PCB.png)
- [PNG export](pcb/PCB.png)

![PCB Layout](pcb/PCB.png)
![PCB Layout](pcb/PCB1.png)


## Photos

![Front view](images/clock_front.jpg)  
![Back view](images/clock_back.jpg)
