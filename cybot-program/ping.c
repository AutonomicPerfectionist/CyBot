/*
 * ping.c
 *
 *  Created on: Oct 27, 2021
 *      Author: benhall
 */
#include "ping.h"

volatile enum {LOW, HIGH, DONE} state; // set by ISR
volatile unsigned int rising_time; // pulse start time: set by ISR
volatile unsigned int falling_time; // pulse end time: set by ISR

void TIMER3B_Handler();

/**
 * Initializes ping sensor pin and timer.
 */
void ping_init() {
        SYSCTL_RCGCTIMER_R |= 0x8;          // send clock to Timer 3
        SYSCTL_RCGCGPIO_R |= 0x2;           // send clock to port B

        GPIO_PORTB_DIR_R &= ~0x8;           // set as input
        GPIO_PORTB_DEN_R |= 0x8;            // enable digital function
        GPIO_PORTB_AFSEL_R |= 0x8;          // enable alternate function
        GPIO_PORTB_PCTL_R |= 0x7000;        // set PB3 to T3CCP1

        TIMER3_CTL_R &= ~0x100;             // disable TIMER3B during configuration

        timer_waitMillis(5);

        TIMER3_CFG_R = 0x4;                 // split into Timer A & B
        TIMER3_TBMR_R = ( TIMER3_TBMR_R | 0x7 ) & 0x7; // set to capture, edge-time mode
        TIMER3_CTL_R |= 0xC00;              // trigger interrupt on both edges
        TIMER3_TBPR_R = 0xFF;                // set pre-scale value
        TIMER3_TBILR_R = 0xFFFF;            // set pre-scale value

        timer_waitMillis(5);

        TIMER3_CTL_R |= 0x100;              // re-enable TIMER3B

        timer_waitMillis(5);
        NVIC_EN1_R |= 0x10;                 // enable interrupt vector 36;

        timer_waitMillis(5);

        IntRegister(INT_TIMER3B, TIMER3B_Handler);  // bind ISR
        IntMasterEnable();                          // start ISR

}

/**
 * Sends initial ping pulse and switches to input on pin.
 */
void send_pulse() {


    TIMER3_CTL_R &= ~0x100; //Stop counting
    TIMER3_IMR_R &= ~0x400; //Disable interrupt for CBEIM
    GPIO_PORTB_AFSEL_R &= ~0b1000; //Select software controlled
    GPIO_PORTB_DIR_R |= 0b1000; // Set PB3 as output
    GPIO_PORTB_DATA_R &= ~0b1000;//Set low
    timer_waitMicros(2);
    GPIO_PORTB_DATA_R |= 0b1000;// Set PB3 to high
    // wait at least 5 microseconds based on data sheet
    timer_waitMicros(10);
    GPIO_PORTB_DATA_R &= ~0b1000;// Set PB3 to low
    GPIO_PORTB_DIR_R &= ~0b1000;// Set PB3 as input
    GPIO_PORTB_AFSEL_R |= 0b1000; //Select alternate function
    state = LOW;
    TIMER3_ICR_R |= 0x400; //Clear interrupt
    TIMER3_IMR_R |= 0x400; //Enable interrupt for CBEIM
    TIMER3_CTL_R |= 0x100; //Start counting
}

int num_overflows = 0;

/**
 * Get distance from ping sensor, in delta cycles.
 */
float ping_read(){
        send_pulse();
        int timeout = 0;
        while (state != DONE && timeout < 10000) {timeout++;}
        if (timeout >= 10000) { return 1000.0; }
        unsigned int delta = rising_time - falling_time;
        return (float) delta;

}

/**
 * ISR for timer.
 */
void TIMER3B_Handler() {

    if((TIMER3_MIS_R & 0x400) == 0)
        return; //Interrupt was not capture event

    TIMER3_ICR_R |= 0x400; //Clear interrupt

    if(state == LOW) {
        rising_time = TIMER3_TBR_R;
        state = HIGH;
    } else if (state == HIGH) {
        falling_time = TIMER3_TBR_R;
        state = DONE;
    }
}
