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
static PyObject* tiny(PyObject* self, PyObject* args)  
{ 
        PyArrayObject* parr; 
        int dims[1]; 
        int i; 
        char *xx; 
	xx = malloc(sizeof(char)*4096); 
        get_pru_data(xx);

	int *data; 

        dims[0] = 4096; 
        parr = (PyArrayObject*) PyArray_FromDims(1, dims, 'i'); 
        if(!parr) return 0; 

        data = (int*) parr->data; 
        for(i=0; i<5; ++i) 
        data[i] = xx[i]; 

        return PyArray_Return(parr); 
}


int get_pru_data(char* dataArray)
{
        // declare variables

        int fd;
        void *map_base, *virt_addr, *rel_addr;
        off_t target; 
        unsigned long current_mem_loc;
        unsigned long b_len;

        printf("BB_MEM_LOC: %x\n", BBB_MEM_LOC);


        // open the memory on BBB

        if((fd = open("/dev/mem", O_RDWR | O_SYNC)) == -1) FATAL; // MB opens memory area to read/write to
        printf("/dev/mem opened.\n"); 
        fflush(stdout);

        // establish the base address  of /dev/mem which displays memory address BBB_MEM_LOC which equates to PRU Memory 
        map_base = mmap(0, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, BBB_MEM_LOC & ~MAP_MASK);

        if(map_base == (void *) -1) FATAL;
        printf("Memory mapped at address %p.\n", map_base); 
        fflush(stdout);

        virt_addr = map_base  + (BBB_MEM_LOC & MAP_MASK);

        current_mem_loc  = *((unsigned long *) virt_addr);

        printf("current memory location: %x\n",current_mem_loc);


        int i=0;
	int temp;
        dataArray[i]  = *((unsigned long *) virt_addr );
        printf("dataArray[%x]: %x\n", i, dataArray[i]);
        


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
                printf("dataArray[%x]: %x\n", i, dataArray[i]);
        }


//        free(buffer);

        return 1234;





}





static PyMethodDef functions[] =
{
        {"tiny", tiny, METH_VARARGS, "example"},
        {0, 0, 0, 0}
};

PyMODINIT_FUNC initpypru(void) 
{
        import_array();
        (void) Py_InitModule("pypru", functions); 
}
