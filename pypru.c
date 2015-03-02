/* To do:

- re name tiny()
- sort out storage and passing of the current address variable
- add switching on /off the pru
- check memory management
- add second  pru/ read both in one pru
- add comments/ description

*/


#include <Python.h>
#include <numpy/arrayobject.h>

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <fcntl.h>  //MB open(), close()#include <sys/mman.h> //MB mmap()
#include <sys/types.h> // MB to define off_t ?? 
#include <sys/mman.h> //MB mmap()

#define MAP_SIZE 4096UL
#define BBB_MEM_LOC 0x4a300000
#define MAP_MASK (MAP_SIZE - 1) // MB map that when bitwise AND'd to and address allow through just the offset to the base address, also AND to ~ MAP_MASK separates out the base address
#define FATAL do { fprintf(stderr, "Error at line %d, file %s (%d) [%s]\n",  __LINE__, __FILE__, errno, strerror(errno)); exit(1); } while(0)



// returns an array
static PyObject* get_pru_data(PyObject* self, PyObject* args)
{
	// Allocate a C array (c_arr) to hold contents of Pru memory, obtained via read_pru_memory()
        char *c_arr;
	int current_mem_loc;
	c_arr = malloc(sizeof(char)*4096);
        current_mem_loc = read_pru_memory(c_arr);

//        printf("current memory location: %x\n",current_mem_loc);
	
	// Create a python array (p_arr) consisting of doubles to store the data from c_arr
        PyArrayObject* p_arr;
        int dims[1];
        dims[0] = MAP_SIZE;
        p_arr = (PyArrayObject*) PyArray_FromDims(1, dims, 'i');
        if(!p_arr) 
	{
		printf("p_arr not created\n");		
		return 0;
	}

	// Create a pointer to the data in the p_arr (p_arr_data) and transfer data from  c_arr to p_arr_data
	int  *p_arr_data;
        p_arr_data = (int*)p_arr->data;

	p_arr_data[0] = current_mem_loc;
	p_arr_data[1] = 0xFFFFFFFF;
	p_arr_data[2] = 0xFFFFFFFF;
	p_arr_data[3] = 0xFFFFFFFF;

        int i;
        for(i=4; i<current_mem_loc; ++i) 
	{
		p_arr_data[i] = c_arr[i];	
	}
//	printf("*******************************************************************\n");

/*	for (i= 0;i < current_mem_loc;i++)
	{
		printf("p_arr_data[%d]: %d\n",i, p_arr_data[i]);
	}
*/
	// free c_arr
	free(c_arr);

	// return the python array (p_arr)
        return PyArray_Return(p_arr); 
}


int read_pru_memory(char* dataArray)
{
        // declare variables

        off_t target; 

        printf("BB_MEM_LOC: %x\n", BBB_MEM_LOC);

	// MB opens memory area to read/write to referenced by fd
        int fd;
        if((fd = open("/dev/mem", O_RDWR | O_SYNC)) == -1) FATAL; 
        printf("/dev/mem opened.\n"); 
        fflush(stdout);

        // establish the base address (map_base) of /dev/mem which displays memory address BBB_MEM_LOC which equates to PRU Memory 
        void *map_base;
        map_base = mmap(0, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, BBB_MEM_LOC & ~MAP_MASK);
        if(map_base == (void *) -1) FATAL;
        printf("Memory mapped at address %p.\n", map_base); 
        fflush(stdout);


	// sets up pointer for begining of pru memory in dev/mem/ (virt_addr) and for a relative address (rel_addr)
        void  *virt_addr, *rel_addr;
        virt_addr = map_base  + (BBB_MEM_LOC & MAP_MASK);
        
	unsigned long current_mem_loc;
        current_mem_loc  = *((unsigned long *) virt_addr); // set current_mem_loc to point to the address at the first 4 bytes (unsigned long) of pru memory 

	int i;
	int temp;
        for(i = 4; i< current_mem_loc; i++)
        {
                rel_addr = virt_addr + i;
                temp = *((char *) rel_addr );  
                if(temp >0)
                {
                        dataArray[i] = 1;
                }else
                {
                        dataArray[i] = 0;
                }
//                printf("dataArray[%x]: %x\n", i, dataArray[i]);
        }
        return current_mem_loc;
}





static PyMethodDef functions[] =
{
        {"get_pru_data", get_pru_data, METH_VARARGS, "example"},
        {0, 0, 0, 0}
};

PyMODINIT_FUNC initpypru(void) 
{
        import_array();
        (void) Py_InitModule("pypru", functions); 
}
