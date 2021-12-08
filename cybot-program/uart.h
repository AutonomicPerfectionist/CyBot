#ifndef CYBOT_UART_H_
#define CYBOT_UART_H_

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <inc/tm4c123gh6pm.h>

extern volatile char receive_data;

//Whether we are currently moving,
//updated in ISR so isn't missed
extern volatile bool inAction;

// Initialize the UART to communciate between CyBot and PuTTy
void uart_init(int BAUD_RATE);

// Send a byte over the UART from CyBot and PuTTy (Buad Rate 115200, No Parity, No Flow Control)
void uart_sendByte(char data);

void uart_handler();

void uart_interrupt_init();

void sendUartString( char msg[] );

#endif /* CYBOT_UART_H_ */
