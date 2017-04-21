/* Akshaal (C) 2010, GNU GPL. http://akshaal.info */

#ifndef AVR_INFO_H_
#define AVR_INFO_H_

#include "sim_avr.h"

/**
 * Like printf but also shows some debug info about avr.
 */
void avr_info (struct avr_t * avr, char *fmt, ...);

#endif /* AVR_INFO_H_ */
