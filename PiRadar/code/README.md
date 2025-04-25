# PiRadar 🔭📡

A semicircular radar system powered by a Raspberry Pi 5, using an ultrasonic sensor and micro servo. Real-time sweep visuals with object detection shown as pulsing blips, rendered using Pygame.

## 🔧 Features

- Smooth servo sweep between **30° and 150°**
- Real-time object detection with HC-SR04 ultrasonic sensor
- Clean semi-circular radar interface with grid rings and distance labels
- Pulsing green blips for objects closer than 120 cm
- **Configurable detection range** — distance threshold and max view distance can be adjusted in code
- Optimized for HDMI output and fullscreen mode

## 💻 Requirements

- Raspberry Pi 5 running Ubuntu
- Python 3.12+
- SG90 micro servo (GPIO 17)
- HC-SR04 ultrasonic sensor (TRIG=23, ECHO=24)
- External 5V power supply for servo
- Python libraries:
  - `pygame`
  - `lgpio`

## 🚀 Run It

```bash
git clone https://github.com/ArvinGhaloosian/PiRadar.git
cd PiRadar
python3 radar_display.py
