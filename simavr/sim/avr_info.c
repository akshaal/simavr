/* Akshaal (C) 2010, GNU GPL. http://akshaal.info */

#include <stdarg.h>
#include <stdio.h>
#include <unistd.h>
#include "avr_info.h"

static avr_cycle_count_t last_cycles = 0;

/**
 * Like printf but also shows some debug info about avr.
 */
void avr_info (struct avr_t * avr, char *fmt, ...) {
    char buf[2048];

    va_list ap;

    va_start (ap, fmt);
    vsnprintf (buf, 2047, fmt, ap);
    va_end (ap);

    avr_cycle_count_t diff = avr->cycle - last_cycles;
    avr_cycle_count_t ns = 1000000000L * diff / avr->frequency;
    avr_cycle_count_t us = ns / 1000L;
    avr_cycle_count_t ms = us / 1000L;
    printf ("+%lu (%lu ms, %lu us, %lu ns): %s", diff, ms, us % 1000L, ns % 1000L, buf);
    fflush (stdout);

    last_cycles = avr->cycle;
}


