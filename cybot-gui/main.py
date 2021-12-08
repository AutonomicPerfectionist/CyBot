import serial.serialutil
import pygame, math, sys, uart, serial, threading, time, numpy
from scipy.optimize import curve_fit
from statistics import pstdev

# Constants
BLUE = (25, 25, 200)
PURPLE = (150, 25, 200)
BLACK = (23, 23, 23)
GREY = (56, 56, 56)
WHITE = (254, 254, 254)
RED = (200, 25, 25)
GREEN = (25, 200, 25)

CM_TO_PX = 1.724
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

move_avg = [14]
turn_avg = [70.12]
ir_cal = [1043, 745, 610, 487, 2191, 1530, 1169, 945, 778, 672, 583, 528, 466, 406, 381, 330, 298, 268, 248, 225, 236, 235, 196, 235, 196, 168, 144, 166, 120]
pg_cal = [16.12, 22.64, 27.04, 31.84, 7.79, 11.29, 14.86, 19.04, 23.14, 26.72, 28.85, 33.23, 36.98, 40.65, 44.12, 48.08, 51.49, 26.79, 33.26, 39.66, 66.9, 1000.0, 1000.0, 1000.0, 1000.0, 64.08, 8.82, 1000.0, 69.69]

configs = {
    3: {'COEFF':  67040.0548282411, 'PWR': -1.0002365394867478},
    9: {'COEFF': 86338.93790129754, 'PWR': -1.0514768371387075}
}

#Which Cybot we're using
CYBOT_NUM = 3
COEFF = configs[CYBOT_NUM]['COEFF']
PWR = configs[CYBOT_NUM]['PWR']


IR_RAW = 0
CliffData = []

def polar_to_cart(deg, amt):
    """Convert polar coordinates to cartesian"""
    x = float(amt) * math.sin(math.radians(int(deg)))
    y = float(amt) * math.cos(math.radians(int(deg)))
    return x,y

def line_of_best_fit():
    """Set formula for calculating ir values"""

    def objective(x, a, b):
	    return a * pow(x, b)
    global COEFF, PWR
    popt, _ = curve_fit(objective, ir_cal, pg_cal)
    COEFF, PWR = popt
    print("COEFF = " + str(COEFF))
    print("PWR = " + str(PWR))

def ir_to_cm(val):
    """Convert ir values into centimeters"""
    return COEFF * pow(val,PWR)

def get_dist(x1,x2,y1,y2):
    """Find distance between two points"""
    return abs(math.sqrt(pow(x1-x2,2) + pow(y1-y2,2)))

def avg(list):
    """Find average value in a list or list-like object"""
    return sum(list) / len(list)

class Player():
    """Cybot player class"""

    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.servo_pos = 0
        self.rot = 90.0
        self.size = 34.8 * CM_TO_PX
        self.rect = pygame.Rect(self.x-30,self.y-30,60,60)
        self.manual = True
        self.lBump = ""
        self.rBump = ""
        self.estimating = False

    def position(self, angle, dist):
        """Update position info"""
        self.rot += angle

        # movement handling
        x, y = polar_to_cart(self.rot, dist * CM_TO_PX)
        self.x += x
        self.y += y
        self.rect = pygame.Rect(self.x-(self.size/2),self.y-(self.size/2),self.size,self.size)


    def bump(self, leftBump, rightBump):
        """Update bumper status on gui and draw"""
        if leftBump == 1:
            x, y = polar_to_cart(self.rot + 45, self.size / 1.5)
            self.lBump = "left "
            CliffData.append(Cliff(False, self.x + x, self.y + y, self.x, self.y, bump=True))
        else: self.lBump = ""

        if rightBump == 1:
            x, y = polar_to_cart(self.rot - 45, self.size / 1.5)
            self.rBump = "right "
            CliffData.append(Cliff(False, self.x + x, self.y + y, self.x, self.y, bump=True))
        else: self.rBump = ""

    def cliff(self, cliffVal) :
        """Cliff handling"""
        lx, ly = polar_to_cart(self.rot + 45, self.size / 1.5)
        flx, fly = polar_to_cart(self.rot + 15, self.size / 1.5)
        rx, ry = polar_to_cart(self.rot - 45, self.size / 1.5)
        frx, fry = polar_to_cart(self.rot - 15, self.size / 1.5)

        if cliffVal & 0b1:
            # l high
            CliffData.append(Cliff(False,self.x + lx,self.y + ly,self.x,self.y))
        if cliffVal & 0b10:
            # l low
            CliffData.append(Cliff(True,self.x + lx,self.y + ly,self.x,self.y))
        if cliffVal >> 2 & 0b1:
            # lf high
            CliffData.append(Cliff(False,self.x + flx,self.y + fly,self.x,self.y))
        if cliffVal >> 2 & 0b10:
            # lf low
            CliffData.append(Cliff(True,self.x + flx,self.y + fly,self.x,self.y))
        if cliffVal >> 4 & 0b1:
            # r high
            CliffData.append(Cliff(False,self.x + rx,self.y + ry,self.x,self.y))
        if cliffVal >> 4 & 0b10:
            # r low
            CliffData.append(Cliff(True,self.x + rx,self.y + ry,self.x,self.y))
        if cliffVal >> 8 & 0b1:
            # rf high
            CliffData.append(Cliff(False,self.x + frx,self.y + fry,self.x,self.y))
        if cliffVal >> 8 & 0b10:
            # rf low
            CliffData.append(Cliff(True,self.x + frx,self.y + fry,self.x,self.y))

    def calibrate_ir(self):
        """Auto-calibrate ir sensor w/ ping sensor"""
        print("Calibrating IR sensors...")
        while self.lBump == "" and self.rBump == "":
            cybot_uart.send_data('w')
            time.sleep(0.25)
            cybot_uart.send_data('w') # stop moving

        time.sleep(0.1)
        
        for _ in range(20):
            cybot_uart.send_data('s')
            time.sleep(0.25)
            cybot_uart.send_data('s')
            cybot_uart.send_data('m')
            time.sleep(0.5)
            if ScanData[len(ScanData) - 1].pg[0] >= 500: continue
            ir_cal.append(IR_RAW)
            pg_cal.append(ScanData[len(ScanData) - 1].pg[0])
        print("Complete!")
        print("Recommend: Find line of best fit (f).")

    def forward(self):
        """Move forward until key isn't pressed"""
        self.estimating = True
        cybot_uart.send_data('w')
        while self.estimating: continue
        cybot_uart.send_data('w')

    def back(self):
        """Move backward until key isn't pressed."""
        self.estimating = True
        cybot_uart.send_data('s')
        while self.estimating: continue
        cybot_uart.send_data('s')

    def left(self):
        """Turn left until key isn't pressed."""
        self.estimating = True
        cybot_uart.send_data('a')
        while self.estimating: continue
        cybot_uart.send_data('a')

    def right(self):
        """Turn right until key isn't pressed/"""
        self.estimating = True
        cybot_uart.send_data('d')
        while self.estimating: continue
        cybot_uart.send_data('d')

    def clear(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.rot = 0
        self.rect = pygame.Rect(self.x-30,self.y-30,60,60)
        ScanData.clear()


    def scan(self,theta,ir,pg):
        """Process results of single scan point"""
        global IR_RAW

        self.servo_pos = theta
        IR_RAW = int(ir)  # for calibration
        ir = ir_to_cm(ir)
        irx, iry = polar_to_cart(int(self.servo_pos) - 90 + self.rot, ir * CM_TO_PX)
        pgx, pgy = polar_to_cart(int(self.servo_pos) - 90 + self.rot, pg * CM_TO_PX)
        offsetx, offsety = polar_to_cart(self.rot, float(34.8 / 2) * CM_TO_PX)
        
        #Cutoff for IR sensor, in cm
        if ir < 65:

            ScanData.append(Point(self.x+irx+offsetx, self.y+iry+offsety, self.x+pgx+offsetx, self.y+pgy+offsety,ir,pg))

            #Average IR and Ping for more accurate results
            avg_x = (self.x+pgx+offsetx + self.x+irx+offsetx) / 2
            avg_y = (self.y+pgy+offsety + self.y+iry+offsety) / 2

            #Add obstacle to grid at calculated coordinates
            obstacle_grid[avg_x][avg_y] = Obstacle(self.x+irx+offsetx, self.y+iry+offsety, avg_x, avg_y)

            print(obstacle_grid)

class Point():
    """Class to hold scan data"""

    def __init__(self,irx,iry,pgx,pgy,ir,pg):
        self.ir = [ir,[irx,iry]]
        self.pg = [pg,[pgx,pgy]]

class Obstacle():
    """
    This represents an obstacle in the field.
    Contains a PointCloud object holding all points determined to be a part of this object.
    """

    def __init__(self, ix, iy, px, py):
        self.ix = ix
        self.iy = iy
        self.px = px
        self.py = py
        self.points = PointCloud((px, py))
    def __str__(self):
        return "Obstacle(" + str(self.px) + ", " + str(self.py) + ", irx: " + str(self.ix) + ", iry: " + str(self.iy) + ")"

    def __repr__(self):
        return self.__str__()


class PointCloud(list):
    """
    Represents a point cloud that defines an obstacle. Dynamically calculates centerpoint,
    and automatically rejects outlier points using calculated Z-score.
    """

    def __init__(self, center):
        super().__init__(self)
        self.least_point = None
        self.most_point = None
        self.center = center

    def append(self, item):
        """
        All the magic happens here. Calculates Z-score for point being appended, automatically
        rejects if outside bounds. If within bounds, appends and recalculates centerpoint.
        """
        distance = math.hypot(item[0] - self.center[0], item[1] - self.center[1])

        if(len(self) > 1):

            x_stdev = pstdev([a[0] for a in self])
            y_stdev = pstdev([a[1] for a in self])

            if(x_stdev != 0 and y_stdev != 0):

                x_score = (item[0] - self.center[0]) / x_stdev # x
                y_score = (item[1] - self.center[1]) / y_stdev # 
                print(x_score)
                print(y_score)
                if(x_score > 8 or y_score > 8):
                    return

        super().append(item)

        #Update centerpoint
        x = [p[0] for p in self]
        y = [p[1] for p in self]
        self.center = (sum(x) / len(self), sum(y) / len(self)) #mew char


        #Update points used for diameter calculations.
        if self.least_point == None or (item[0] < self.least_point[0] and item[1] < self.least_point[1]):
            self.least_point = item

        if self.most_point == None or (item[0] > self.most_point[0] and item[1] > self.most_point[1]):
            self.most_point = item


class Grid():
    '''
    Class for transparently working on the grid.

    Acts similar to 2d list. If grid[a] does not exist, the inner list is automatically created.
    Index into the grid like so: grid[x][y].
    If no obstacle exists at (x,y), returns None.

    When adding to inner list, first looks at locations within near_threshold to see if obstacle already exists.
    '''

    def __init__(self, near_threshold=5, outer=True, container=None):
        self.grid_dict = {}
        self.near_threshold = near_threshold
        self.outer = outer
        self.container = container
        self.points = []

    def get_obstacles(self):
        obstacles = []
        for row in self.grid_dict.values():
            for obst in row.grid_dict.values():
                obstacles.append(obst)
        return obstacles

    def clear(self):
        del self.grid_dict
        self.grid_dict = {}

    def __getitem__(self, key):
        """
        If key does not exist and is outer, create inner Grid() at key.
        If key does not exist and is inner, return None.
        """
        key = int(key)
        try:
            return self.grid_dict[key]
        except KeyError:
            if(self.outer):
                self.grid_dict[key] = Grid(near_threshold=self.near_threshold,outer=False, container = self)
                return self.grid_dict[key]
            return None

    def __setitem__(self, key, newval):
        """
        Looks at values near key to determine if an obstacle is nearby, if
        so, then add to that obstacle's point cloud instead of adding to grid.
        Otherwise, add to grid.
        """

        if(not self.outer):
            x = int(newval.px)
            y = int(newval.py)
            for i in range(int(x - self.near_threshold), int(x + self.near_threshold)):
                for j in range(int(y - self.near_threshold), int(y + self.near_threshold)):
                    if self.container[i][j] != None:
                        self.container[i][j].points.append((newval.px, newval.py))
                        return

            #If no near obstacle found, add to grid
            self.grid_dict[int(key)] = newval
    
    def __str__(self):
        return str(self.grid_dict)

    def __repr__(self):
        return self.__str__()

class Cliff():
    """Class to hold cliff or bumper data"""

    def __init__(self,cliff,x,y,dX,dY, bump=False):
        if cliff:
            self.color = BLACK
        elif not bump:
            self.color = WHITE
        else:
            self.color = GREEN

        self.x = x
        self.y = y
        self.dx = dX
        self.dy = dY


# initalize pygame
pygame.init()
font = pygame.font.SysFont('Segoe UI', 30)
screen = pygame.display.set_mode((1920, 1080), pygame.RESIZABLE)
ScanData = []

#Optimized near_threshold for obstacle size.
obstacle_grid = Grid(near_threshold=32)

try:
    cybot_uart = uart.UartConnection()
    player = Player()
    stream = threading.Thread(target=cybot_uart.data_stream, args=[player])
    stream.daemon = True
    stream.start()
except serial.serialutil.SerialException:
    print("No serial connection found")
    sys.exit()

fast_mode = False
running = True

#Main program loop
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
                cybot_uart.send_data("n")
            if event.key == ord('c'): # calibrate
                threading.Thread(target=player.calibrate_ir).start()
            if event.key == ord('f'): # apply calibration settings
                line_of_best_fit()
            if event.key == ord('k'): # clear scan data
                ScanData.clear()
                obstacle_grid.clear()
            if event.key == ord('r'): # reset cybot location
                pass
            if(event.key == ord('p')): # toggle speed mode
                cybot_uart.send_data("p")
                fast_mode = not fast_mode
        elif event.type == pygame.KEYUP:
            player.estimating = False

    # fill background
    screen.fill(GREY)

    #Draw cliff/bumper objects
    for cliff in CliffData:
        pygame.draw.circle(screen, cliff.color, (cliff.x, cliff.y), 10)

    # draw cybot
    xe, ye = polar_to_cart(player.rot + player.servo_pos - 90, player.size / 2)
    pygame.draw.circle(screen, WHITE, (player.x, player.y), player.size / 2)
    pygame.draw.arc(screen, GREEN, player.rect, math.radians(player.rot-180), math.radians(player.rot), 10)
    pygame.draw.line(screen, BLUE, (player.x, player.y), (player.x + xe, player.y + ye), 5)
    bump_text = font.render("bumper: " + player.lBump + player.rBump, False, WHITE)
    screen.blit(bump_text,(0,40))
    pos_text = font.render(str(round(player.x - (SCREEN_WIDTH / 2), 2)) + ", " + str(round(player.y - (SCREEN_HEIGHT / 2),2)) + ", " + str(round(player.rot,2)), False, WHITE)
    screen.blit(pos_text,(0,80))


    #Draw text status of auto mode
    if player.manual:
        mode_text = font.render("mode: manual", False, WHITE)
    else:
        mode_text = font.render("mode: auto", False, WHITE)
    screen.blit(mode_text,(0,0))

    #Draw text status of speed mode
    if(fast_mode):
        fast_text = font.render("speed: 150", False, WHITE)
    else:
        fast_text = font.render("speed: 50", False, WHITE)
    screen.blit(fast_text, (0, 160))

    #Draw scanned objects, calculating radius from point cloud least and most points
    for obstacle in obstacle_grid.get_obstacles():
            if(obstacle.points.least_point == None or obstacle.points.most_point == None):
                continue
            x2 = obstacle.points.most_point[0]
            x1 = obstacle.points.least_point[0]
            y2 = obstacle.points.most_point[1]
            y1 = obstacle.points.least_point[1]
            pygame.draw.circle(screen, RED, obstacle.points.center, math.hypot(x2 - x1, y2 - y1) / 2)
    
   # print(str(obstacle_grid) + "\n")

    pygame.display.flip()
