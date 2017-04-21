SHELL	 = /bin/bash
MCU=attiny85

sources		:= $(wildcard *.c)

all : ${sources:.c=.pytest}

include ../Makefile.common

%.pytest: %.hex
	./${<:.hex=.py}

clean:
	rm -f *.hex *.o *.axf *.s
