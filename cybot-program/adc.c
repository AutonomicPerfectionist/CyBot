#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <timer.h>
#include <inc/tm4c123gh6pm.h>

/**
 * Initialize the ADC,
 * using hardware averaging
 */
void adc_init(void){

    SYSCTL_RCGCGPIO_R |= 0x2; // sets clock for GPIO port B
    SYSCTL_RCGCADC_R |= 0x1; // turns on clock for ADC
    timer_waitMillis(10);
    GPIO_PORTB_AFSEL_R |= 0x10; // turn on alternate function for PB4
    GPIO_PORTB_AMSEL_R |= 0x10; // analog for pb4
    GPIO_PORTB_DEN_R &= ~(0x10); // turn off digital function for PB4
    GPIO_PORTB_DIR_R &= ~(0x10); // turns PB4 into an input
    GPIO_PORTB_ADCCTL_R |= 0x10; // says PB4 is a pin used to trigger the ADC [optional?]
    ADC0_ACTSS_R &= ~(0x1); // disable ss0 before configuration
    ADC0_EMUX_R &= ~(0xF); // clear emux before configuration
    ADC0_SSMUX0_R &= ~(0xF); // clear first 4 bits in MUX0
    ADC0_SSMUX0_R |= 0xA; // first sample is AIN10
    ADC0_SSCTL0_R = 0x6; // 1st sample is the last sample of the sequence
    ADC0_ACTSS_R |= 0x1; // now that we have configured ss0, we can enable it
}

/**
 * Sample on IR sensor and return direct ADC value.
 */
int adc_read(void) {

    ADC0_PSSI_R = 0x1; // begin sampling on ss0
    while((ADC0_RIS_R & 0x1) == 0); // waiting for data
    int ir_data = ADC0_SSFIFO0_R;
    ADC0_ISC_R |= 0x1; // clear interrupt ss0

    return ir_data;
}
