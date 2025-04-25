## 📡 PiRadar

A real-time semicircular radar interface built with Python and Pygame.  
Uses a Raspberry Pi 5, SG90 servo, and HC-SR04 ultrasonic sensor to sweep from 30° to 150° and visualize nearby objects as pulsing blips.

- Smooth servo sweep via `lgpio`
- Real-time distance readings with `HC-SR04`
- Semi-circular HUD with distance rings
- Blips for objects under 120 cm
- Optimized for HDMI display

![PiRadar Demo](PiRadar/assets/radar_demo.gif)
