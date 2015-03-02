// PRUSS program to read wheel encoder values and store them in a cyclic 
// memory buffer in PRU memory 
//

.origin 0                        // start of program in PRU memory
.entrypoint START                // program entry point (for a debugger)

#define INS_PER_SAMPLE_LOOP   20000         // @5ns per instruction => 0.1ms sample/ 10kHz
#define INS_PER_DELAY_LOOP 2     // two instructions per delay loop
#define INS_TO_TAKE_SAMPLE	8	// time take to perform sample

#define DELAY   (INS_PER_SAMPLE_LOOP - INS_TO_TAKE_SAMPLE) / INS_PER_DELAY_LOOP  

#define PRU0_R31_VEC_VALID 32    // allows notification of program completion
#define PRU_EVTOUT_0    3        // the event number that is sent back

START:

	MOV 	r0, 0x0		// Set SAMPDELAY counter to 0
	MOV 	r1, DELAY	// Set SAMPDELAY constant value 
	MOV	r2, 0x03	// Set latest sample address to 8
	MOV	r3, 0x00000000	// Address to track latest sample address	


MAINLOOP:
	ADD 	r2, r2, 1 	// increment sample counter
	QBEQ	RESET, r2.b1, 0x10 // reset at 4096 ie 0x1000



	SBBO	r2, r3, 0, 4	// write sample counter to mem address 0x00000000
	
	MOV	r4, r31.b0	// read sample value into REG4
	SBBO	r4, r2, 0, 1	// write sample value to sample address counter
	
	MOV	r0, r1
	MOV	r0, r1		// duplicate instruction to create 8 step sample
SAMPD:
        SUB     r0, r0, 1        // Decrement REG1 by 1
        QBNE    SAMPD, r0, 0   // Loop to SAMPDELAY, unless REG0=0

        QBBC    MAINLOOP, r31.t0 // is the button pressed? If not, loop	


END:                             // notify the calling app that finished
	MOV	R31.b0, PRU0_R31_VEC_VALID | PRU_EVTOUT_0
	HALT                     // halt the pru program

RESET:
	MOV	r2, 0x03 	// reset back to start of sample buffer
	QBA	MAINLOOP


