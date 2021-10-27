import serial.serialutil
import pygame, math, sys, uart, serial, threading, time

# Constants
BLUE = (25, 25, 200)
PURPLE = (200, 25, 200)
BLACK = (23, 23, 23)
WHITE = (254, 254, 254)
RED = (200, 25, 25)
GREEN = (25, 200, 25)

CM_TO_PX = 1.724
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
EST_DIST = 3.67
EST_ANGLE = 17.53

def polar_to_cart(deg, amt):
    """convert polar coordinates to cartesian"""
    x = float(amt) * math.sin(math.radians(int(deg)))
    y = float(amt) * math.cos(math.radians(int(deg)))
    return x,y

def ir_to_cm(val):
    """convert ir values into centimeters"""
    return 2600000 * pow(float(val),-1.56)

def get_dist(x1,x2,y1,y2):
    return abs(math.sqrt(pow(x1-x2,2) + pow(y1-y2,2)))

class Player():
    """cybot player class"""

    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.servo_pos = 0
        self.rot = 90.0
        self.size = 34.8 * CM_TO_PX
        self.rect = pygame.Rect(self.x-30,self.y-30,60,60)
        self.manual = True
        self.bumper = ""
        self.estimating = False

    def update(self, angle, dist):
        """update position info"""
        self.rot += angle

        x, y = polar_to_cart(self.rot, dist * CM_TO_PX)
        self.x += x
        self.y += y
        self.rect = pygame.Rect(self.x-(self.size/2),self.y-(self.size/2),self.size,self.size)

    def estimate_move(self):
        cybot_uart.send_data('w')
        time.sleep(0.25)
        cybot_uart.send_data('w')

    def estimate_turn(self):
        cybot_uart.send_data('a')
        time.sleep(0.25)
        cybot_uart.send_data('a')

    def forward(self):
        self.estimating = True
        dist = 0
        cybot_uart.send_data('w')
        while self.estimating:
            self.update(0, EST_DIST)
            dist -= EST_DIST
            time.sleep(0.25)
        cybot_uart.send_data('w')
        self.update(0, dist)

    def back(self):
        self.estimating = True
        dist = 0
        cybot_uart.send_data('s')
        while self.estimating:
            self.update(0, (-1)*EST_DIST)
            dist += EST_DIST
            time.sleep(0.25)
        cybot_uart.send_data('s')
        self.update(0, dist)

    def left(self):
        self.estimating = True
        angle = 0
        cybot_uart.send_data('a')
        while self.estimating:
            self.update(EST_ANGLE, 0)
            angle -= EST_ANGLE
            time.sleep(.25)
        cybot_uart.send_data('a')
        self.update(angle, 0)

    def right(self):
        self.estimating = True
        angle = 0
        cybot_uart.send_data('d')
        while self.estimating:
            self.update((-1)*EST_ANGLE, 0)
            angle += EST_ANGLE
            time.sleep(.25)
        cybot_uart.send_data('d')
        self.update(angle, 0)

    def clear(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.rot = 0
        self.rect = pygame.Rect(self.x-30,self.y-30,60,60)
        ScanData.clear()

    def radial_scan(self):
        """do radial scan"""
        start_theta = self.rot
        while abs(self.rot - start_theta) <= 360:
            cybot_uart.send_data('m')
            cybot_uart.send_data('a')
            time.sleep(.1)
            cybot_uart.waiting = True
            cybot_uart.send_data('a')


    def scan(self,ir,pg):
        """scan 180 degrees infront"""

        ir = ir_to_cm(ir)
        irx, iry = polar_to_cart(self.rot, ir * CM_TO_PX)
        pgx, pgy = polar_to_cart(self.rot, pg * CM_TO_PX)
        offsetx, offsety = polar_to_cart(self.rot, float(34.8 / 2) * CM_TO_PX)
        ScanData.append(Point(self.x+irx+offsetx, self.y+iry+offsety, self.x+pgx+offsetx, self.y+pgy+offsety,ir,pg))  

class Point():
    """class to hold scan data"""

    def __init__(self,irx,iry,pgx,pgy,ir,pg):
        self.ir = [ir,[irx,iry]]
        self.pg = [pg,[pgx,pgy]]

# initalize serial connection
try:
    cybot_uart = uart.UartConnection()
    player = Player()
    stream = threading.Thread(target=cybot_uart.data_stream, args=[player])
    stream.daemon = True
    stream.start()
except serial.serialutil.SerialException:
    print("ERR: Failed to connect to CyBot.")
    sys.exit()

# initalize pygame
pygame.init()
font = pygame.font.SysFont('Segoe UI', 30)
screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
ScanData = []
RenderedScan = []

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            try:
                sys.exit()
            finally:
                main = False

        if event.type == pygame.KEYDOWN:
            if event.key == ord('a'): # turn left
                threading.Thread(target=player.left).start()
            if event.key == ord('d'): # turn right
                threading.Thread(target=player.right).start()
            if event.key == ord('w'): # move forward
                threading.Thread(target=player.forward).start()
            if event.key == ord('s'): # move backwards
                threading.Thread(target=player.back).start()
            if event.key == ord('m'): # scan once
                cybot_uart.send_data("m")
            if event.key == ord('n'): # radial scan
                threading.Thread(target=player.radial_scan).start()
            if event.key == ord('u'):
                threading.Thread(target=player.estimate_move).start()
            if event.key == ord('i'):
                threading.Thread(target=player.estimate_turn).start()
        elif event.type == pygame.KEYUP:
            player.estimating = False

    # fill background
    screen.fill(BLACK)

    # draw cybot
    xe, ye = polar_to_cart(player.rot + player.servo_pos - 90, player.size / 2)
    pygame.draw.circle(screen, WHITE, (player.x, player.y), player.size / 2)
    pygame.draw.arc(screen, GREEN, player.rect, math.radians(player.rot-180), math.radians(player.rot), 10)
    pygame.draw.line(screen, BLUE, (player.x, player.y), (player.x + xe, player.y + ye), 5)
    bump_text = font.render("bumper: " + player.bumper, False, WHITE)
    screen.blit(bump_text,(0,40))
    pos_text = font.render(str(round(player.x - (SCREEN_WIDTH / 2), 2)) + ", " + str(round(player.y - (SCREEN_HEIGHT / 2),2)) + ", " + str(round(player.rot,2)), False, WHITE)
    screen.blit(pos_text,(0,80))

    if player.manual:
        mode_text = font.render("mode: manual", False, WHITE)
    else:
        mode_text = font.render("mode: auto", False, WHITE)
    screen.blit(mode_text,(0,0))

    RenderedScan.clear()
    start = 0
    end = 0
    for x in range(len(ScanData)):
        pygame.draw.circle(screen, RED, ScanData[x].ir[1], 1)
        if ScanData[x].ir[0] < 180 and ScanData[x].pg[0] < 300:
            end = x
        elif (abs(start - end) >= 3):
            RenderedScan.append([ScanData[start].pg[1],ScanData[int((start+end)/2)].pg[1],ScanData[end].pg[1]])
            start = x + 1
            end = x + 1
        else:
            start = x + 1
            end = x + 1
    
    for points in RenderedScan:
        pygame.draw.polygon(screen, WHITE, points, 5)


    pygame.display.flip()