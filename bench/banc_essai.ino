/*
  Banc d'essai moteur — Dassault UAV Challenge, équipe ISEP
  Carte : Arduino Nano Every (ou Uno/Nano). Mesures : poussée (HX711 + cellule 20 kg, bras 3:1),
  tension et courant batterie (diviseur + ACS758-50B ou module INA226 avec shunt externe),
  régime (capteur optique IR sur une pale), commande ESC par PWM 50 Hz (Servo.h).
  Sortie : CSV sur le port série à 115200 bauds, une ligne par 100 ms :
    t_ms,cmd_us,thrust_g,volt_V,curr_A,power_W,rpm,g_per_W
  Sécurité : la rampe de gaz ne démarre qu'après l'appui sur le bouton START (D7), s'arrête
  immédiatement si le bouton STOP (D8) est relâché (homme mort) ou si la liaison série reçoit 's'.

  Bibliothèques Arduino à installer : "HX711 Arduino Library" (Bogdan Necula), "Servo" (intégrée).
  Câblage (voir notice) :
    HX711  DT -> D2, SCK -> D3, VCC 5 V, GND
    ESC signal -> D9 (Servo), masse commune ESC/Arduino OBLIGATOIRE, l'ESC n'alimente pas l'Arduino
    Diviseur tension batterie (100 k / 10 k) -> A0  (6S max 25,2 V -> 2,29 V)
    ACS758-50B (ou sortie analogique courant) -> A1 ; alimenté en 5 V
    Capteur IR TCRT5000 (sortie numérique) -> D5 (interruption externe)
    Bouton START -> D7 (vers GND, pull-up interne) ; Bouton STOP homme mort -> D8 (vers GND, pull-up)
*/
#include <Servo.h>
#include "HX711.h"

// ---------- réglages à adapter ----------
const float LEVER_RATIO     = 3.0f;      // bras 300 mm au-dessus de l'axe / 100 mm en dessous
float       CAL_FACTOR      = 1.0f;      // facteur HX711 : lu après la procédure d'étalonnage (commande 'c')
const float VDIV_RATIO      = 11.0f;     // (100k + 10k) / 10k
const float ADC_REF_V       = 5.0f;      // Nano Every : 5 V (vérifier au multimètre)
const float ACS_SENS_V_PER_A = 0.040f;   // ACS758-50B : 40 mV/A, zéro à 2,5 V
const int   BLADES          = 3;         // nombre de pales vues par le capteur optique par tour
const int   ESC_MIN_US = 1000, ESC_MAX_US = 2000;
const int   STEP_US = 50, STEP_HOLD_MS = 4000;   // rampe : +50 µs toutes les 4 s
const int   RAMP_MAX_US = 1800;                  // plafond de la rampe automatique (on ne va pas au max sans décision humaine)
const float CURR_LIMIT_A = 40.0f;                // coupure si le courant dépasse (protège le pack 1P au banc)

// ---------- matériel ----------
const int PIN_HX_DT = 2, PIN_HX_SCK = 3, PIN_ESC = 9, PIN_RPM = 5, PIN_START = 7, PIN_STOP = 8, PIN_V = A0, PIN_I = A1;
Servo esc; HX711 scale;
volatile unsigned long pulseCount = 0;
void onPulse() { pulseCount++; }

enum State { IDLE, ARMING, RAMP, STOPPED };
State state = IDLE;
int cmd_us = ESC_MIN_US;
unsigned long tState = 0, tLog = 0, tRpm = 0;
unsigned long lastPulses = 0;
float acsZero = 2.5f;

float readVolt() { return analogRead(PIN_V) * ADC_REF_V / 1023.0f * VDIV_RATIO; }
float readCurr() { return (analogRead(PIN_I) * ADC_REF_V / 1023.0f - acsZero) / ACS_SENS_V_PER_A; }
float readThrustG() { return scale.get_units(1) / LEVER_RATIO; }   // get_units renvoie des grammes après étalonnage

void stopAll(const char* why) {
  esc.writeMicroseconds(ESC_MIN_US); cmd_us = ESC_MIN_US; state = STOPPED;
  Serial.print(F("# STOP: ")); Serial.println(why);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_START, INPUT_PULLUP); pinMode(PIN_STOP, INPUT_PULLUP); pinMode(PIN_RPM, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_RPM), onPulse, FALLING);
  esc.attach(PIN_ESC, ESC_MIN_US, ESC_MAX_US); esc.writeMicroseconds(ESC_MIN_US);   // armement ESC : gaz mini au démarrage
  scale.begin(PIN_HX_DT, PIN_HX_SCK); scale.set_scale(CAL_FACTOR); delay(500); scale.tare(20);
  // zéro du capteur de courant, moteur à l'arrêt
  long acc = 0; for (int i = 0; i < 100; i++) { acc += analogRead(PIN_I); delay(2); }
  acsZero = acc / 100.0f * ADC_REF_V / 1023.0f;
  Serial.println(F("# Banc d'essai ISEP. Commandes: 's' stop, 't' tare, 'c' etalonnage (poser une masse connue), 'r' lancer la rampe (START maintenu)"));
  Serial.println(F("t_ms,cmd_us,thrust_g,volt_V,curr_A,power_W,rpm,g_per_W"));
  state = IDLE; tState = millis();
}

void loop() {
  unsigned long now = millis();
  // ---- sécurité : homme mort et série
  if (digitalRead(PIN_STOP) == HIGH && state == RAMP) stopAll("bouton homme mort relache");
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 's') stopAll("commande serie");
    else if (c == 't') { scale.tare(20); Serial.println(F("# tare OK")); }
    else if (c == 'c') {
      Serial.println(F("# Etalonnage: suspendez une masse connue au plateau moteur (poulie, traction vers +x), puis envoyez la masse en grammes"));
      while (!Serial.available()) {}
      float known = Serial.parseFloat();
      float raw = scale.get_value(20);                 // valeur brute moyenne, tare déduite
      CAL_FACTOR = raw / (known * LEVER_RATIO);        // la cellule voit 3 x la masse
      scale.set_scale(CAL_FACTOR);
      Serial.print(F("# CAL_FACTOR = ")); Serial.println(CAL_FACTOR, 4);
    }
    else if (c == 'r' && (state == IDLE || state == STOPPED)) { state = ARMING; tState = now; Serial.println(F("# armement 3 s, maintenez STOP enfonce")); }
  }
  // ---- machine à états
  if (state == ARMING && now - tState > 3000) {
    if (digitalRead(PIN_START) == LOW && digitalRead(PIN_STOP) == LOW) { state = RAMP; cmd_us = ESC_MIN_US + 100; tState = now; }
    else if (now - tState > 10000) { state = IDLE; Serial.println(F("# START non appuye, retour IDLE")); }
  }
  if (state == RAMP) {
    if (now - tState > (unsigned long)STEP_HOLD_MS) { cmd_us += STEP_US; tState = now; }
    if (cmd_us > RAMP_MAX_US) stopAll("fin de rampe");
    esc.writeMicroseconds(cmd_us);
  }
  // ---- régime : comptage sur 200 ms
  static float rpm = 0;
  if (now - tRpm >= 200) {
    noInterrupts(); unsigned long p = pulseCount; interrupts();
    rpm = (p - lastPulses) * (60000.0f / 200.0f) / BLADES; lastPulses = p; tRpm = now;
  }
  // ---- journal CSV à 10 Hz
  if (now - tLog >= 100) {
    tLog = now;
    float th = readThrustG(), v = readVolt(), i = readCurr(), pw = v * i;
    if (i > CURR_LIMIT_A && state == RAMP) stopAll("courant > limite");
    Serial.print(now); Serial.print(','); Serial.print(cmd_us); Serial.print(',');
    Serial.print(th, 0); Serial.print(','); Serial.print(v, 2); Serial.print(','); Serial.print(i, 2); Serial.print(',');
    Serial.print(pw, 1); Serial.print(','); Serial.print(rpm, 0); Serial.print(',');
    Serial.println(pw > 1 ? th / pw : 0, 2);
  }
}
