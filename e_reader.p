// PRUSS program to read wheel encoder values and store them in a cyclic 
// memory buffer in PRU memory 
//

.origin 0                        // start of program in PRU memory
.entrypoint START                // program entry point (for a debugger)

#define INS_PER_US   200         // 5ns per instruction
#define INS_PER_DELAY_LOOP 2     // two instructions per delay loop
                                 // set up a 50ms delay
#define DELAY  100 * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP) 

#define PRU0_R31_VEC_VALID 32    // allows notification of program completion
#define PRU_EVTOUT_0    3        // the event number that is sent back

START:

	MOV 	r0, 0x0		// Set SAMPDELAY counter to 0
	MOV 	r1, DELAY	// Set SAMPDELAY constant value 
	MOV	r2, 0x04	// Set Sample counter to 0
	MOV	r3, 0x00000000	// Set sample counter address	
	MOV	r4, 10		// pretend sample


MAINLOOP:
	ADD 	r2, r2, 1 	// increment sample counter
	SBBO	r2, r3, 0, 4	// write sample counter to mem address 0x00000000

	
	MOV	r0, r1
SAMPD:
        SUB     r0, r0, 1        // Decrement REG1 by 1
        QBNE    SAMPD, r0, 0   // Loop to SAMPDELAY, unless REG0=0

        QBBC    MAINLOOP, r31.t2 // is the button pressed? If not, loop	


END:                             // notify the calling app that finished
	MOV	R31.b0, PRU0_R31_VEC_VALID | PRU_EVTOUT_0
	HALT                     // halt the pru program
