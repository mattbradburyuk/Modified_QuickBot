// PRUSS program to read wheel encoder values and store them in a cyclic 
// memory buffer in PRU memory 
//

.origin 0                        // start of program in PRU memory
.entrypoint START                // program entry point (for a debugger)

#define INS_PER_US   200         // 5ns per instruction
#define INS_PER_DELAY_LOOP 2     // two instructions per delay loop
                                 // set up a 50ms delay
#define DELAY  50 * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP) 

#define PRU0_R31_VEC_VALID 32    // allows notification of program completion
#define PRU_EVTOUT_0    3        // the event number that is sent back

START:
	MOV 	r0, DELAY

MAINLOOP:
	SET 	r30.t0
	MOV	r1, r0
DELAYON:
        SUB     r1, r1, 1        // Decrement REG1 by 1
        QBNE    DELAYON, r1, 0   // Loop to DELAYON, unless REG1=0
LEDOFF:
	CLR	r30.t0
        MOV     r1, r0        // Reset REG1 to the length of the delay
DELAYOFF:
        SUB     r1, r1, 1        // decrement REG1 by 1
        QBNE    DELAYOFF, r1, 0  // Loop to DELAYOFF, unless REG0=0

        QBBC    MAINLOOP, r31.t2 // is the button pressed? If not, loop	


END:                             // notify the calling app that finished
	MOV	R31.b0, PRU0_R31_VEC_VALID | PRU_EVTOUT_0
	HALT                     // halt the pru program
