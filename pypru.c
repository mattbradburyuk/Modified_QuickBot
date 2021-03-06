/* To do:

- check memory management
- add second  pru/ read both in one pru
- add comments/ description

*/

// for intacting with python 
#include <Python.h>
#include <numpy/arrayobject.h>

#include <stdio.h>
#include <stdlib.h>

#define TRUE 1
#define FALSE 0

// for reading the pru
#include <errno.h>
#include <fcntl.h>  //MB open(), close()#include <sys/mman.h> //MB mmap()
#include <sys/types.h> // MB to define off_t ?? 
#include <sys/mman.h> //MB mmap()

#define MAP_SIZE 4096UL
#define BBB_MEM_LOC 0x4a300000
#define MAP_MASK (MAP_SIZE - 1) // MB map that when bitwise AND'd to and address allow through just the offset to the base address, also AND to ~ MAP_MASK separates out the base address
#define FATAL do { fprintf(stderr, "Error at line %d, file %s (%d) [%s]\n",  __LINE__, __FILE__, errno, strerror(errno)); exit(1); } while(0)

// for starting and ending the pru
#include </usr/include/prussdrv.h> // pru interface
#include </usr/include/pruss_intc_mapping.h> // pru mapping info

#define PRU_NUM 0   // using PRU0 for these examples


// declare functions - 
static PyObject* start_up_pru(PyObject* self, PyObject* args);
static PyObject* stop_pru(PyObject* self, PyObject* args);
static PyObject* get_pru_data(PyObject* self, PyObject* args);
int read_pru_memory(char* dataArray_0, char* data_array_1);



// define functions callable from python

static PyMethodDef functions[] =
{
        {"get_pru_data", get_pru_data, METH_VARARGS, "Gets data from pru"},
        {"start_up_pru", start_up_pru, METH_VARARGS, "starts up pru"},
        {"stop_pru", stop_pru, METH_VARARGS, "stops pru"},
        {0, 0, 0, 0}
};

// define initalisation of the module

PyMODINIT_FUNC initpypru(void) 
{
        import_array();
        (void) Py_InitModule("pypru", functions); 
}




// start up the pru
static PyObject* start_up_pru(PyObject* self, PyObject* args)
{
	   if(getuid()!=0)
	   {
	   	printf("You must run this program as root. Exiting.\n");
	   	exit(EXIT_FAILURE);
	   }

	// Initialize structure used by prussdrv_pruintc_intc
	// PRUSS_INTC_INITDATA is found in pruss_intc_mapping.h
	tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;

	// Allocate and initialize memory
	prussdrv_init ();
	prussdrv_open (PRU_EVTOUT_0);

   	// Map PRU's interrupts
   	prussdrv_pruintc_init(&pruss_intc_initdata);

   	// Load and execute the PRU program on the PRU
   	prussdrv_exec_program (PRU_NUM, "./e_reader.bin");

	Py_RETURN_NONE;

}

//stop the pru
static PyObject* stop_pru(PyObject* self, PyObject* args)
{
   	// Disable PRU and close memory mappings
   	prussdrv_pru_disable(PRU_NUM);
   	prussdrv_exit ();
   	Py_RETURN_NONE;;

}



// gets the pru memory dataand passes it to back to python as a numpy ndarray
static PyObject* get_pru_data(PyObject* self, PyObject* args)
{
	// Allocate a C array (c_arr) to hold contents of Pru memory, obtained via read_pru_memory()
        char *c_arr_0, *c_arr_1;
	int current_mem_loc;
	c_arr_0 = malloc(sizeof(char)*4096);
	c_arr_1 = malloc(sizeof(char)*4096);
        current_mem_loc = read_pru_memory(c_arr_0,c_arr_1);

//        printf("current memory location: %x\n",current_mem_loc);
	
	// Create a python array (p_arr) consisting of doubles to store the data from c_arr
        PyArrayObject* p_arr;
        int dims[2];
        dims[0] = 2;
	dims[1] = MAP_SIZE;
        p_arr = (PyArrayObject*) PyArray_FromDims(2, dims, 'i');
        if(!p_arr) 
	{
		printf("p_arr not created\n");		
		return 0;
	}

//	printf("number of dimensions: %d\n", PyArray_NDIM(p_arr));

	// Create a pointer to the data in the p_arr (p_arr_data) and transfer data from  c_arr to p_arr_data
	int  *p_arr_data;
        p_arr_data = (int*)p_arr->data;
/*
	printf("ptr to [0,0]: %p\n" , PyArray_GETPTR2(p_arr,0,0));
	printf("ptr to [0,1]: %p\n" , PyArray_GETPTR2(p_arr,0,1));
	printf("ptr to [1,0]: %p\n" , PyArray_GETPTR2(p_arr,1,0));
	printf("ptr to [1,1]: %p\n" , PyArray_GETPTR2(p_arr,1,1));
*/

	p_arr_data[0] = current_mem_loc;
	p_arr_data[1] = 0xFFFFFFFF;
	p_arr_data[2] = 0xFFFFFFFF;
	p_arr_data[3] = 0xFFFFFFFF;
	p_arr_data[0 + MAP_SIZE] = current_mem_loc;
	p_arr_data[1 + MAP_SIZE] = 0xFFFFFFFF;
	p_arr_data[2 + MAP_SIZE] = 0xFFFFFFFF;
	p_arr_data[3 + MAP_SIZE] = 0xFFFFFFFF;

        int i;
        for(i=4; i<MAP_SIZE; ++i) 
	{
		p_arr_data[i] = c_arr_0[i];	
		p_arr_data[i + MAP_SIZE] = c_arr_1[i];

	}
//	printf("*******************************************************************\n");
/*
	for (i= 0;i < MAP_SIZE;i++)
	{
		printf("p_arr_data[%x]: %d\n",(i/4), p_arr_data[i]);
	}
*/
	// free c_arr
	free(c_arr_0);
	free(c_arr_1);

	// return the python array (p_arr)
        return PyArray_Return(p_arr); 
}


int read_pru_memory(char* dataArray_0, char* dataArray_1)
{
        // declare variables

        off_t target; 

//        printf("BB_MEM_LOC: %x\n", BBB_MEM_LOC);

	// MB opens memory area to read/write to referenced by fd
        int fd;
        if((fd = open("/dev/mem", O_RDWR | O_SYNC)) == -1) FATAL; 
//        printf("/dev/mem opened.\n"); 
        fflush(stdout);

        // establish the base address (map_base) of /dev/mem which displays memory address BBB_MEM_LOC which equates to PRU Memory 
        void *map_base;
        map_base = mmap(0, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, BBB_MEM_LOC & ~MAP_MASK);
        if(map_base == (void *) -1) FATAL;
//        printf("Memory mapped at address %p.\n", map_base); 
        fflush(stdout);


	// sets up pointer for begining of pru memory in dev/mem/ (virt_addr) and for a relative address (rel_addr)
        void  *virt_addr, *rel_addr;
        virt_addr = map_base  + (BBB_MEM_LOC & MAP_MASK);
        
	unsigned long current_mem_loc;
        current_mem_loc  = *((unsigned long *) virt_addr); // set current_mem_loc to point to the address at the first 4 bytes (unsigned long) of pru memory 

	int i;
	int temp;
	int error = FALSE;
        for(i = 4; i< MAP_SIZE; i++)
        {
                rel_addr = virt_addr + i;
                temp = *((char *) rel_addr );  
                if(temp == 0)
                {
                        dataArray_0[i] = 0;
                        dataArray_1[i] = 0;
		}else if (temp == 1)
		{
                        dataArray_0[i] = 1;
                        dataArray_1[i] = 0;
                }else if (temp == 2)
                {
                        dataArray_0[i] = 0;
                        dataArray_1[i] = 1;
                }else if (temp == 3)
                {
		        dataArray_0[i] = 1;
                        dataArray_1[i] = 1;
		}else
		{
			error = TRUE;
		}


//                printf("dataArray[%x]: %x\n", i, dataArray[i]);
	}

	if(error) printf("error memory locations do not contain 1s and 0s");

	close(fd);

        return current_mem_loc;
}

