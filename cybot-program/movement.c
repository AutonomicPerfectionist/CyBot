#include "movement.h"

#include <stdio.h>
#include "open_interface.h"
#include "Timer.h"
#include "lcd.h"
#include "uart.h"

/**
 * Moves forward by requested centimeters.
 */
double move(oi_t *sensor, int centimeters){
    // moves the bot [centimeters]
    // centimeters > 0 = forwards, centimeters < 0 = backwards

    double sum = 0;
    char returnString[20];
    int mod = 1;

    if (centimeters > 0) {
        oi_setWheels(100, 100);
        mod = 1;
    } else {
        oi_setWheels(-100, -100);
        mod = -1;
    }
    while (sum < abs(centimeters*10) ) {
        oi_update(sensor);
        sum += abs(sensor->distance);
    }
    sprintf(returnString,"MOV,%0.4f\n",(sum / 10) * mod);
    sendUartString(returnString);
    oi_setWheels(0, 0); // stop
    return centimeters;
}

/**
 * Turns requested number of degrees.
 */
double turn(oi_t *sensor, double degrees){
    // turns the bot [degrees]
    // neg # = right
    // pos # = left

    char returnString[20];
    double currAngle = 0;

    if (degrees < 0) {
        oi_setWheels(-50, 50); // turn clockwise
        while (currAngle > degrees ) {
            oi_update(sensor);
            currAngle += sensor->angle;
        }
    } else {
        oi_setWheels(50, -50); // turn co-clockwise
        while (currAngle < degrees ) {
            oi_update(sensor);
            currAngle += sensor->angle;
        }
    }
    sprintf(returnString,"TRN,%0.2f\n",(float) currAngle);
    sendUartString(returnString);
    oi_setWheels(0, 0); // stop
    return degrees;
}

/**
 * Moves and automatically avoids any objects detected by bump sensor.
 */
void moveAndAvoid(oi_t *sensor, double returnDist) {
    int sideOffset = 0;
    float totalDist = 0;
    char returnString[20];

    while (totalDist < returnDist*10) {
        oi_setWheels(50, 50);
        oi_update(sensor);
        if (sensor->bumpLeft) {
            sendUartString("BMP,-1\n");
            sprintf(returnString,"MOV,%0.2f\n",((float)sensor->distance / 10));
            sendUartString(returnString);

            move(sensor, -10);
            sendUartString("BMP,0\n");

            turn(sensor, -90);
            move(sensor, 25);
            turn(sensor, 90);

            returnDist += 150; //account for extra movement
            sideOffset += 25; //account for side offset
        }
        else if(sensor->bumpRight) {
            sendUartString("BMP,1\n");
            sprintf(returnString,"MOV,%0.2f\n",((float)sensor->distance / 10));
            sendUartString(returnString);

            move(sensor, -10);
            sendUartString("BMP,0\n");

            turn(sensor, 90);
            move(sensor, 25);
            turn(sensor, -90);

            returnDist += 150; //account for extra movement
            sideOffset -= 25; //account for side offset
        } else {
            sprintf(returnString,"MOV,%0.2f\n",((float)sensor->distance / 10));
            sendUartString(returnString);
        }
        totalDist += sensor->distance;
    }
    if (sideOffset > 0) {
        turn(sensor,90);
        move(sensor,abs(sideOffset));
    } else if (sideOffset < 0) {
        turn(sensor,-90);
        move(sensor,abs(sideOffset));
    }
}
