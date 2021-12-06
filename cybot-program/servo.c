#include "servo.h"

volatile float servo_pos;
float servo_correction = 0;
float servo_coefficient = 1;

void servo_init()
{
    //    SYSCTL_RCGCGPIO_R |= 0x2;                   // send clock on port B
    //    SYSCTL_RCGCTIMER_R |= 0x2;                  // send clock on TIMER1
    //
    //    timer_waitMillis(5);
    //
    //    GPIO_PORTB_DIR_R |= 0x20;                   // set PB5 as output
    //    GPIO_PORTB_DEN_R |= 0x20;                   // set PB5 as digital
    //    GPIO_PORTB_AFSEL_R |= 0x20;                 // use alt func on PB5
    //    GPIO_PORTB_PCTL_R |= 0x00700000;            // pctl
    //
    //    TIMER1_CTL_R &= ~0x100;                      // disable TIMER1B
    //    TIMER1_CFG_R |= 0x4;                        // set to 16bit
    //    TIMER1_TBMR_R |= 0xA;                        // set to periodic
    //
    //    TIMER1_TBPR_R = 320000 >> 16;               // set timer prescaler
    //    TIMER1_TBILR_R = 320000;                    // set period

    //GPIO

    SYSCTL_RCGCGPIO_R |= 0b10; //enable port b
    SYSCTL_RCGCTIMER_R |= 0b10; //enables timer 1
    timer_waitMillis(10);
    GPIO_PORTB_DEN_R |= 0x20; // enable digital functions of wire 5
    GPIO_PORTB_DIR_R |= 0x20; // turn wire 5 into output
    GPIO_PORTB_AFSEL_R |= 0x20; // enable alt func wire 5
    GPIO_PORTB_PCTL_R &= ~0xF00000; //Clear wire 5
    GPIO_PORTB_PCTL_R |= 0x700000; //Set port control to 7, i.e. T1CCP1

    //TIMER


    TIMER1_CTL_R &= ~0x100; // disable timer b while init
    TIMER1_CFG_R = 0x00000004; // select 16 bit timer config
    TIMER1_TBMR_R |= 0xA; // periodic timer mode, pwm enabled, edge count mode
    TIMER1_CTL_R &= ~0x4000; // output is standard/not inverted
    TIMER1_TBPR_R = 0x4; // prescale value = 4
    TIMER1_TBILR_R = 0xE200; // 800 in dec, start 20 ms between pwm waves
    TIMER1_TBMATCHR_R = 0xA380; // high for 5% of 20ms
    TIMER1_TBPMR_R = 0x4;
    TIMER1_CTL_R |= 0x100; // re-enable timer b
    servo_pos = 0;

    //    TIMER1_CTL_R |= 0x100;                      // enable TIMER1B
}

void servo_move(float degrees)
{
    servo_pos = degrees;

    //Correct requested for calibration
    degrees += servo_correction;
    degrees *= servo_coefficient;

    //    TIMER1_CTL_R &= ~0x100;                  // disable TIMER1B
    //
    //    int match_value = ( (0.0095*(degrees) + .5) / 0.0000625);
    //
    //    TIMER1_TBMATCHR_R = ( 320000 - match_value ) & 0xFFFF;
    //    TIMER1_TBPMR_R = ( 320000 - match_value) >> 16;
    //
    //    TIMER1_CTL_R |= 0x100;                  // enable TIMER1B

    TIMER1_CTL_R &= ~0x100; // disable timer b while init
    TIMER1_TBR_R = TIMER1_TBILR_R;
    TIMER1_TBPR_R = 0x4;
    float millis = ((degrees / 180)*1.5) + 0.75;
    int cycles = (320000 - ((millis / 20) * 320000)) ;
    TIMER1_TBMATCHR_R = cycles & 0xFFFF;
    TIMER1_TBPMR_R = cycles >> 16;
    TIMER1_CTL_R |= 0x100; // re-enable timer b
}

void servo_set_calibration(float correction, float coefficient) {
    servo_correction = correction;
    servo_coefficient = coefficient;
}
