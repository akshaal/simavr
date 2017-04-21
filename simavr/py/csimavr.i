/* Akshaal (C) 2010, GNU GPL. http://akshaal.info */

%module csimavr

#define  __attribute__(x)

%{
#include "fifo_declare.h"
#include "sim_avr.h"
#include "sim_avr_types.h"
#include "sim_regbit.h"
#include "avr_adc.h"
#include "avr_eeprom.h"
#include "avr_extint.h"
#include "avr_flash.h"
#include "avr_info.h"
#include "avr_ioport.h"
#include "avr_spi.h"
#include "avr_timer.h"
#include "avr_twi.h"
#include "avr_uart.h"
#include "avr_watchdog.h"
#include "sim_core.h"
#include "sim_cycle_timers.h"
#include "sim_elf.h"
#include "sim_gdb.h"
#include "sim_hex.h"
#include "sim_interrupts.h"
#include "sim_io.h"
#include "sim_irq.h"
#include "sim_time.h"
#include "sim_vcd_file.h"
%}

%include "stdint.i"

/* - - - - Includes - - - - - */

%include "fifo_declare.h"
%include "sim_regbit.h"
%include "avr_adc.h"
%include "avr_eeprom.h"
%include "avr_extint.h"
%include "avr_flash.h"
%include "avr_info.h"
%include "avr_ioport.h"
%include "avr_spi.h"
%include "avr_timer.h"
%include "avr_twi.h"
%include "avr_uart.h"
%include "avr_watchdog.h"
%include "sim_avr.h"
%include "sim_avr_types.h"
%include "sim_core.h"
%include "sim_cycle_timers.h"
%include "sim_elf.h"
%include "sim_gdb.h"
%include "sim_hex.h"
%include "sim_interrupts.h"
%include "sim_io.h"
%include "sim_irq.h"
%include "sim_time.h"
%include "sim_vcd_file.h"

/* - - - Custom stuff - - - */

%include "carrays.i"
%array_class(struct ihex_chunk_t, ihex_chunk_t_array);

/* avr_t */

%nodefaultdtor avr_t;
%extend avr_t {
    avr_t (const char *name) {
        return avr_make_mcu_by_name(name);
    }

    ~avr_t () {
    }
}

/* avr_irq_t */

%nodefaultdtor avr_irq_t;
%extend avr_irq_t {
    avr_irq_t (avr_irq_pool_t * pool, uint32_t base, uint32_t count) {
        return avr_alloc_irq (pool, base, count, NULL);
    }

    ~avr_irq_t () {
    }

    avr_irq_t *_get_by_index (int index) {
        return self + index;
    }
}

%inline %{
    void __avr_ireq_notify_runner__ (struct avr_irq_t *irq, uint32_t value, void *param) {
        PyObject *param_casted = (PyObject*) param;

        PyObject *this = PyTuple_GetItem (param_casted, 0);
        if (this == NULL) {
            PyErr_Print ();
            return;
        }

        Py_INCREF (this);

        PyObject *cb = PyObject_GetAttrString (this, "_notify_handler");

        PyObject *arglist = Py_BuildValue ("(Ol)", param, (long)value);

        PyObject_Repr(param_casted);
        PyObject *result = PyEval_CallObject (cb, arglist);

        Py_DECREF (this);
        Py_DECREF (arglist);
        Py_DECREF (cb);

        if (result == NULL) {
            PyErr_Print ();
        } else {
            Py_DECREF (result);
        }
    }

    void avr_irq_register_notify_py (avr_irq_t *irq, PyObject *param) {
        avr_irq_register_notify (irq, &__avr_ireq_notify_runner__, param);
    }
%}

/* avr_cycle_timer_t */

/* This is a way to pass callback from python. Don't use unless you know what you are doing! */
%inline %{
    avr_cycle_count_t __avr_cycle_timer_runner__ (struct avr_t *avr,
                                                  avr_cycle_count_t when,
                                                  void *param)
    {
        PyObject *this = (PyObject*) param;

        PyObject *cb = PyObject_GetAttrString (this, "_timer_handler");
        PyObject *arglist = Py_BuildValue ("()");

        PyObject *result = PyEval_CallObject (cb, arglist);

        Py_DECREF (arglist);
        Py_DECREF (cb);

        unsigned long long ret = 0;
        if (result == NULL) {
            PyErr_Print ();
        } else {
            if (SWIG_AsVal_unsigned_SS_long_SS_long (result, &ret) != SWIG_OK) {
                ret = 0;
            }

            Py_DECREF (result);
        }

        return (avr_cycle_count_t) ret;
    }

    void avr_cycle_timer_register_py (avr_t *avr, avr_cycle_count_t when, PyObject *param)
    {
        avr_cycle_timer_register (avr, when, &__avr_cycle_timer_runner__, param);
    }

    void avr_cycle_timer_cancel_py (avr_t *avr, PyObject *param)
    {
        avr_cycle_timer_cancel (avr, &__avr_cycle_timer_runner__, param);
    }
%}

/* Other helpers */

%inline %{
    void *unsafe_cast_pyobject_to_void_ptr (PyObject *arg) {
        return arg;
    }

    uint32_t avr_ioctl_ioport_getirq (char name) {
        return AVR_IOCTL_IOPORT_GETIRQ (name);
    }
%}
