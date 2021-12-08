#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <inc/tm4c123gh6pm.h>
#include <math.h>
#include "timer.h"

extern volatile bool inAction = true;
extern volatile char receive_data = '\0';

// Initialize the UART to communciate between CyBot and PuTTy
void uart_init(int BAUD_RATE){
    SYSCTL_RCGCGPIO_R   |= 0b000010;    //enable clock to GPIO, R1 = port B
    SYSCTL_RCGCUART_R   |= 0b000010;    //enable clock to UART1, R1 = UART1.
    GPIO_PORTB_AFSEL_R  |= 0b00000011;  //enable alternate functions on port b pins 0 and 1
    GPIO_PORTB_PCTL_R   |= 0x00000011;  //enable Rx and Tx on port B on pins 0 and 1
    GPIO_PORTB_DEN_R    |= 0b00000011;  //set pin 0 and 1 to digital
    GPIO_PORTB_DIR_R    &= 0b11111110;  //set pin 0 to Rx or input
    GPIO_PORTB_DIR_R    |= 0b00000010;  //set pin 1 to Tx or output

    //calculate baudrate
    double BRD = 16000000.0 / (16.0 * (double) BAUD_RATE);
    uint16_t iBRD = trunc(BRD);
    uint16_t fBRD = (BRD - iBRD) * 64 + 0.5;

    UART1_CTL_R &= 0b1111111111111110;  // turn off uart1 while we set it up

    //set baud rate
    UART1_IBRD_R = iBRD;
    UART1_FBRD_R = fBRD;

    UART1_LCRH_R    = 0b01100000;     //set frame, 8 data bits, 1 stop bit, no parity, no FIFO
    UART1_CC_R      = 0b0000;         //use system clock as source

    UART1_CTL_R |= 0b0000001100000001; //re-enable enable RX, TX, and uart1
}

// Send a byte over the UART from CyBot and PuTTy (Buad Rate 115200, No Parity, No Flow Control)
void uart_sendByte(char data){
    //    while(UART1_FR_R & 0x20) {} // wait until there is room to send data
    //    UART1_DR_R = data;          // send data

    while((UART1_FR_R & 0b100000) != 0);
    UART1_DR_R = data;
    while((UART1_FR_R & 0b1000) != 0);
}

/**
 * ISR for UART. Also sets inAction if needed,
 * so it isn't missed during auto-avoid operations.
 */
void uart_handler() {
    if (UART1_MIS_R & 0b10000) { //check if a receive byte IRQ has occurred

        while (UART1_FR_R & UART_FR_RXFE) {}
        char data = (char) (UART1_DR_R & 0xFF);
        if (data >= 128) { data -= 128; } // detect if character is ASCII
        receive_data = data;

        if(data == 'w' || data == 'a' || data == 's' || data == 'd') {
            inAction = !inAction;
        }

        UART1_ICR_R |= 0b10000; // clear interrupt
    } else if (UART1_MIS_R & 0b100000) {
        UART1_ICR_R |= 0b100000; // clear interrupt
    }
}


/**
 * Set interrupt registers.
 */
void uart_interrupt_init() {
    //    UART1_IM_R |= 0b110000; //enable send and receive raw interrupts
    //    NVIC_EN0_R |= 0b1000000; // enable interrupt for IRQ 6 / UART1 interrupt
    //    IntRegister(INT_UART1, uart_handler); // tell cpu which func to use as the ISR for UART1
    //    IntMasterEnable();

    // Enable interrupts for receiving bytes through UART1
    UART1_IM_R |= 0b10000; //enable interrupt on receive - page 924
    //
    //    // Find the NVIC enable register and bit responsible for UART1 in table 2-9
    //    // Note: NVIC register descriptions are found in chapter 3.4
    NVIC_EN0_R |= 0b1000000; //enable uart1 interrupts - page 104
    //
    //    // Find the vector number of UART1 in table 2-9 ! UART1 is 22 from vector number page 104
    IntRegister(22, uart_handler); //give the microcontroller the address of our interrupt handler - page 104 22 is the vector number
}

/**
 * Convenience function to loop over a string and print each byte.
 */
void sendUartString( char msg[] ) {
    // send string to UART
    int i = 0;
    while ( msg[i] != '\0' ){
        uart_sendByte(msg[i]);
        i++;
    }
}
