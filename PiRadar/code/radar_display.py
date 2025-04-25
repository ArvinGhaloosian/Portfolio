import pygame
import lgpio
import math
import time

# === GPIO Setup ===
CHIP = 0
SERVO_PIN = 17
TRIG = 23
ECHO = 24

h = lgpio.gpiochip_open(CHIP)
lgpio.gpio_claim_output(h, SERVO_PIN)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

def set_angle(angle):
    duty = 5 + (angle / 180.0) * 5  # 5%–10%
    lgpio.tx_pwm(h, SERVO_PIN, 50, duty)
    time.sleep(0.02)

def get_distance():
    lgpio.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    lgpio.gpio_write(h, TRIG, 0)

    timeout = time.time() + 0.05
    while lgpio.gpio_read(h, ECHO) == 0:
        if time.time() > timeout:
            return 999
    start = time.time()

    while lgpio.gpio_read(h, ECHO) == 1:
        if time.time() > timeout:
            return 999
    stop = time.time()

    duration = stop - start
    distance_cm = (duration * 34300) / 2
    return min(distance_cm, 200)

# === Pygame Setup ===
pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("PiRadar Display")
clock = pygame.time.Clock()

center_x = 300
center_y = 390  # Lower so grid fits screen
max_distance = 200  # cm
scale = 1  # 1 pixel = 1 cm

blips = []

def draw_radar(angle, distance):
    screen.fill((0, 0, 0))

    ring_color = (0, 100, 0)
    ring_thickness = 1
    font = pygame.font.SysFont("Arial", 14)
    max_radius = max_distance * scale

    # Draw semicircle rings + labels
    for cm in range(40, max_distance + 1, 40):
        radius = int(cm * scale)
        arc_rect = pygame.Rect(
            center_x - radius, center_y - radius, 2 * radius, 2 * radius
        )
        label_gap = 0.25  # radians to leave clear (~14 degrees)
        pygame.draw.arc(screen, ring_color, arc_rect, label_gap, math.pi - label_gap, ring_thickness)
        label = font.render(f"{cm} cm", True, (0, 255, 0))
        screen.blit(label, (center_x + radius + 5, center_y - 10))

    # Draw center dot for reference
    pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), 3)

    # Draw sweeping line
    rad = math.radians(angle)
    end_x = center_x + int(max_radius * math.cos(rad))
    end_y = center_y - int(max_radius * math.sin(rad))
    pygame.draw.line(screen, (0, 255, 0), (center_x, center_y), (end_x, end_y), 2)

    # Draw pulsing blips
    current_time = time.time()
    for b in blips[:]:
        if current_time - b["time"] > 2:
            blips.remove(b)
            continue
        pulse = int(255 * (1 - (current_time - b["time"]) / 2))
        pygame.draw.circle(screen, (0, pulse, 0), b["pos"], 5)

    # Add new blip if within detection range
    if distance < 120:
        x = center_x + int(distance * scale * math.cos(rad))
        y = center_y - int(distance * scale * math.sin(rad))
        blips.append({"pos": (x, y), "time": current_time})

    pygame.display.update()

# === Main Radar Loop ===
try:
    angle = 30
    direction = 1
    target_loop_time = 0.03  # ~33 frames per second

    while True:
        loop_start = time.time()

        set_angle(angle)
        distance = get_distance()
        draw_radar(angle, distance)

        if angle >= 150:
            direction = -1
        elif angle <= 30:
            direction = 1
        angle += direction

        # Enforce constant loop time
        elapsed = time.time() - loop_start
        if elapsed < target_loop_time:
            time.sleep(target_loop_time - elapsed)

except KeyboardInterrupt:
    print("Exiting radar display.")
    pygame.quit()
    lgpio.gpiochip_close(h)
