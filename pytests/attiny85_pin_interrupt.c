#include <avr/interrupt.h>
#include <avr/io.h>

ISR(PCINT0_vect) {
    // Set LED to 1
    PORTB |= 1 << 3;
}

ISR(TIMER0_COMPA_vect) {
    // Set PIN to 1
    PORTB |= 1 << 0;
}

// Main function
int main () {
    // PB0 as some "PIN"
    PORTB = 0 << 0;  // gnd
    DDRB  = 1 << 0;  // out
    GIMSK |= 1 << PCIE;
    PCMSK |= 1 << PCINT0;

    // PB3 as a "LED"
    PORTB |= 0 << 3; // gnd
    DDRB  |= 1 << 3; // out

    // Setup timer
    OCR0A = 50 - 1;
    TCCR0A = (1 << WGM01); // CTC
    TCCR0B = ((0 << CS02) | (0 << CS01) | (1 << CS00)); // Prescaller = 1
    TIMSK |= (1 << OCIE0A); // Enable channel A of timer 0

    sei();

    while (1) {};
}
