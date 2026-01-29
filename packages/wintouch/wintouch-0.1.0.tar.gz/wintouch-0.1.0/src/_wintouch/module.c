/*
 * wintouch - Python C Extension for Windows Touch Injection API
 *
 * Provides low-level access to InitializeTouchInjection() and InjectTouchInput()
 * for simulating touch events on Windows 8+.
 *
 * Based on Microsoft's official sample:
 * https://learn.microsoft.com/en-us/archive/technet-wiki/6460.windows-8-simulating-touch-input-using-touch-injection-api
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <windows.h>

/* Touch Injection API types - may not be in older headers */
#ifndef POINTER_FLAG_NONE
#define POINTER_FLAG_NONE           0x00000000
#define POINTER_FLAG_NEW            0x00000001
#define POINTER_FLAG_INRANGE        0x00000002
#define POINTER_FLAG_INCONTACT      0x00000004
#define POINTER_FLAG_FIRSTBUTTON    0x00000010
#define POINTER_FLAG_SECONDBUTTON   0x00000020
#define POINTER_FLAG_THIRDBUTTON    0x00000040
#define POINTER_FLAG_FOURTHBUTTON   0x00000080
#define POINTER_FLAG_FIFTHBUTTON    0x00000100
#define POINTER_FLAG_PRIMARY        0x00002000
#define POINTER_FLAG_CONFIDENCE     0x00004000
#define POINTER_FLAG_CANCELED       0x00008000
#define POINTER_FLAG_DOWN           0x00010000
#define POINTER_FLAG_UPDATE         0x00020000
#define POINTER_FLAG_UP             0x00040000
#define POINTER_FLAG_WHEEL          0x00080000
#define POINTER_FLAG_HWHEEL         0x00100000
#define POINTER_FLAG_CAPTURECHANGED 0x00200000
#define POINTER_FLAG_HASTRANSFORM   0x00400000
#endif

#ifndef TOUCH_FLAG_NONE
#define TOUCH_FLAG_NONE             0x00000000
#endif

#ifndef TOUCH_MASK_NONE
#define TOUCH_MASK_NONE             0x00000000
#define TOUCH_MASK_CONTACTAREA      0x00000001
#define TOUCH_MASK_ORIENTATION      0x00000002
#define TOUCH_MASK_PRESSURE         0x00000004
#endif

#ifndef PT_TOUCH
#define PT_TOUCH                    0x00000002
#endif

#ifndef TOUCH_FEEDBACK_DEFAULT
#define TOUCH_FEEDBACK_DEFAULT      0x1
#define TOUCH_FEEDBACK_INDIRECT     0x2
#define TOUCH_FEEDBACK_NONE         0x3
#endif

/* Function pointer types */
typedef BOOL (WINAPI *PFN_InitializeTouchInjection)(UINT32, DWORD);
typedef BOOL (WINAPI *PFN_InjectTouchInput)(UINT32, const POINTER_TOUCH_INFO*);

/* Module state */
static HMODULE hUser32 = NULL;
static PFN_InitializeTouchInjection pfnInitializeTouchInjection = NULL;
static PFN_InjectTouchInput pfnInjectTouchInput = NULL;
static int touch_initialized = 0;
static UINT32 max_contacts = 0;

/* Load touch injection functions dynamically */
static int load_touch_functions(void) {
    if (hUser32 != NULL) {
        return 1;  /* Already loaded */
    }

    hUser32 = LoadLibraryA("user32.dll");
    if (hUser32 == NULL) {
        return 0;
    }

    pfnInitializeTouchInjection = (PFN_InitializeTouchInjection)
        GetProcAddress(hUser32, "InitializeTouchInjection");
    pfnInjectTouchInput = (PFN_InjectTouchInput)
        GetProcAddress(hUser32, "InjectTouchInput");

    if (pfnInitializeTouchInjection == NULL || pfnInjectTouchInput == NULL) {
        FreeLibrary(hUser32);
        hUser32 = NULL;
        pfnInitializeTouchInjection = NULL;
        pfnInjectTouchInput = NULL;
        return 0;
    }

    return 1;
}

/*
 * initialize(max_contacts=1, feedback_mode=TOUCH_FEEDBACK_DEFAULT)
 *
 * Initialize touch injection. Must be called before injecting touch events.
 *
 * Args:
 *     max_contacts: Maximum number of simultaneous touch contacts (1-10)
 *     feedback_mode: Visual feedback mode (FEEDBACK_DEFAULT, FEEDBACK_INDIRECT, FEEDBACK_NONE)
 *
 * Returns:
 *     True on success, raises OSError on failure.
 */
static PyObject* wintouch_initialize(PyObject *self, PyObject *args, PyObject *kwargs) {
    static char *kwlist[] = {"max_contacts", "feedback_mode", NULL};
    UINT32 max_contacts_arg = 1;
    DWORD feedback_mode = TOUCH_FEEDBACK_DEFAULT;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Ik", kwlist, &max_contacts_arg, &feedback_mode)) {
        return NULL;
    }

    if (max_contacts_arg < 1 || max_contacts_arg > 10) {
        PyErr_SetString(PyExc_ValueError, "max_contacts must be between 1 and 10");
        return NULL;
    }

    if (!load_touch_functions()) {
        PyErr_SetString(PyExc_OSError,
            "Touch injection API not available (requires Windows 8+)");
        return NULL;
    }

    if (!pfnInitializeTouchInjection(max_contacts_arg, feedback_mode)) {
        DWORD err = GetLastError();
        PyErr_Format(PyExc_OSError,
            "InitializeTouchInjection failed (error %lu)", err);
        return NULL;
    }

    touch_initialized = 1;
    max_contacts = max_contacts_arg;

    Py_RETURN_TRUE;
}

/*
 * inject(contacts)
 *
 * Inject touch input events.
 *
 * Args:
 *     contacts: List of touch contact dictionaries, each containing:
 *         - x, y: Screen coordinates in pixels (required)
 *         - flags: Pointer flags (required) - use FLAGS_DOWN, FLAGS_UPDATE, FLAGS_UP
 *         - pointer_id: Unique ID for this contact, 0 to max_contacts-1 (optional, default 0)
 *         - pressure: Pressure value 0-32000 (optional, default 32000)
 *         - orientation: Orientation in degrees 0-359 (optional, default 90)
 *         - contact_width: Contact area width in pixels (optional, default 4)
 *         - contact_height: Contact area height in pixels (optional, default 4)
 *
 * Returns:
 *     True on success, raises OSError on failure.
 */
static PyObject* wintouch_inject(PyObject *self, PyObject *args) {
    PyObject *contacts_list;
    Py_ssize_t count;
    POINTER_TOUCH_INFO *contacts_arr = NULL;
    PyObject *result = NULL;

    if (!touch_initialized) {
        PyErr_SetString(PyExc_RuntimeError,
            "Touch injection not initialized. Call initialize() first.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &contacts_list)) {
        return NULL;
    }

    count = PyList_Size(contacts_list);
    if (count == 0) {
        PyErr_SetString(PyExc_ValueError, "contacts list cannot be empty");
        return NULL;
    }
    if (count > (Py_ssize_t)max_contacts) {
        PyErr_Format(PyExc_ValueError,
            "Too many contacts (%zd), maximum is %u", count, max_contacts);
        return NULL;
    }

    /* Allocate and ZERO the array - critical for proper operation */
    contacts_arr = (POINTER_TOUCH_INFO *)calloc(count, sizeof(POINTER_TOUCH_INFO));
    if (contacts_arr == NULL) {
        PyErr_NoMemory();
        return NULL;
    }

    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject *contact_dict = PyList_GetItem(contacts_list, i);
        PyObject *val;
        LONG x, y;
        LONG contact_width = 4;   /* Default: 4 pixel contact area */
        LONG contact_height = 4;

        if (!PyDict_Check(contact_dict)) {
            PyErr_SetString(PyExc_TypeError, "Each contact must be a dictionary");
            goto cleanup;
        }

        /* Required: x coordinate */
        val = PyDict_GetItemString(contact_dict, "x");
        if (val == NULL) {
            PyErr_SetString(PyExc_KeyError, "Contact missing required 'x' key");
            goto cleanup;
        }
        x = (LONG)PyLong_AsLong(val);

        /* Required: y coordinate */
        val = PyDict_GetItemString(contact_dict, "y");
        if (val == NULL) {
            PyErr_SetString(PyExc_KeyError, "Contact missing required 'y' key");
            goto cleanup;
        }
        y = (LONG)PyLong_AsLong(val);

        /* Required: flags */
        val = PyDict_GetItemString(contact_dict, "flags");
        if (val == NULL) {
            PyErr_SetString(PyExc_KeyError, "Contact missing required 'flags' key");
            goto cleanup;
        }

        /* Set up contact exactly as Microsoft sample */
        contacts_arr[i].pointerInfo.pointerType = PT_TOUCH;
        contacts_arr[i].pointerInfo.pointerId = (UINT32)i;  /* Default to index */
        contacts_arr[i].pointerInfo.ptPixelLocation.x = x;
        contacts_arr[i].pointerInfo.ptPixelLocation.y = y;
        contacts_arr[i].pointerInfo.pointerFlags = (DWORD)PyLong_AsUnsignedLong(val);

        /* Touch properties - Microsoft sample defaults */
        contacts_arr[i].touchFlags = TOUCH_FLAG_NONE;
        contacts_arr[i].touchMask = TOUCH_MASK_CONTACTAREA | TOUCH_MASK_ORIENTATION | TOUCH_MASK_PRESSURE;
        contacts_arr[i].orientation = 90;     /* Perpendicular to screen */
        contacts_arr[i].pressure = 32000;     /* Default pressure */

        /* Optional: pointer_id override */
        val = PyDict_GetItemString(contact_dict, "pointer_id");
        if (val != NULL) {
            contacts_arr[i].pointerInfo.pointerId = (UINT32)PyLong_AsUnsignedLong(val);
        }

        /* Optional: pressure override */
        val = PyDict_GetItemString(contact_dict, "pressure");
        if (val != NULL) {
            contacts_arr[i].pressure = (UINT32)PyLong_AsUnsignedLong(val);
        }

        /* Optional: orientation override */
        val = PyDict_GetItemString(contact_dict, "orientation");
        if (val != NULL) {
            contacts_arr[i].orientation = (UINT32)PyLong_AsUnsignedLong(val);
        }

        /* Optional: contact area dimensions */
        val = PyDict_GetItemString(contact_dict, "contact_width");
        if (val != NULL) {
            contact_width = (LONG)PyLong_AsLong(val);
        }
        val = PyDict_GetItemString(contact_dict, "contact_height");
        if (val != NULL) {
            contact_height = (LONG)PyLong_AsLong(val);
        }

        /* Set contact area (centered on touch point) */
        contacts_arr[i].rcContact.left = x - contact_width / 2;
        contacts_arr[i].rcContact.right = x + contact_width / 2;
        contacts_arr[i].rcContact.top = y - contact_height / 2;
        contacts_arr[i].rcContact.bottom = y + contact_height / 2;

        if (PyErr_Occurred()) {
            goto cleanup;
        }
    }

    if (!pfnInjectTouchInput((UINT32)count, contacts_arr)) {
        DWORD err = GetLastError();
        PyErr_Format(PyExc_OSError, "InjectTouchInput failed (error %lu)", err);
        goto cleanup;
    }

    result = Py_True;
    Py_INCREF(result);

cleanup:
    free(contacts_arr);
    return result;
}

/*
 * is_available()
 *
 * Check if touch injection is available on this system.
 *
 * Returns:
 *     True if Windows 8+ and touch injection API is present.
 */
static PyObject* wintouch_is_available(PyObject *self, PyObject *args) {
    if (load_touch_functions()) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

/*
 * is_initialized()
 *
 * Check if touch injection has been initialized.
 */
static PyObject* wintouch_is_initialized(PyObject *self, PyObject *args) {
    if (touch_initialized) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

/*
 * get_max_contacts()
 *
 * Get the maximum number of simultaneous contacts configured.
 */
static PyObject* wintouch_get_max_contacts(PyObject *self, PyObject *args) {
    return PyLong_FromUnsignedLong(max_contacts);
}

/*
 * diagnose()
 *
 * Diagnose touch injection capability and return detailed status.
 *
 * Returns:
 *     Dictionary with diagnostic information about touch injection capability.
 */
static PyObject* wintouch_diagnose(PyObject *self, PyObject *args) {
    PyObject *result = PyDict_New();
    if (result == NULL) return NULL;

    /* System metrics constants */
    #define SM_DIGITIZER 94
    #define SM_MAXIMUMTOUCHES 95
    #define NID_INTEGRATED_TOUCH 0x01
    #define NID_EXTERNAL_TOUCH 0x02
    #define NID_MULTI_INPUT 0x40
    #define NID_READY 0x80

    /* Check API availability */
    int api_available = load_touch_functions();
    PyDict_SetItemString(result, "api_available", api_available ? Py_True : Py_False);

    if (!api_available) {
        PyDict_SetItemString(result, "has_touch_digitizer", Py_False);
        PyDict_SetItemString(result, "digitizer_flags", PyLong_FromLong(0));
        PyDict_SetItemString(result, "max_touch_points", PyLong_FromLong(0));
        PyDict_SetItemString(result, "integrated_touch", Py_False);
        PyDict_SetItemString(result, "external_touch", Py_False);
        PyDict_SetItemString(result, "touch_ready", Py_False);
        PyDict_SetItemString(result, "init_works", Py_False);
        PyDict_SetItemString(result, "init_error", PyLong_FromLong(0));
        PyDict_SetItemString(result, "inject_works", Py_False);
        PyDict_SetItemString(result, "inject_error", PyLong_FromLong(0));
        PyDict_SetItemString(result, "diagnosis",
            PyUnicode_FromString("Touch injection API not available. Requires Windows 8 or later."));
        return result;
    }

    /* Get system metrics for touch capability */
    int digitizer = GetSystemMetrics(SM_DIGITIZER);
    int max_touches = GetSystemMetrics(SM_MAXIMUMTOUCHES);

    int has_touch = (digitizer & (NID_INTEGRATED_TOUCH | NID_EXTERNAL_TOUCH)) != 0;
    int integrated = (digitizer & NID_INTEGRATED_TOUCH) != 0;
    int external = (digitizer & NID_EXTERNAL_TOUCH) != 0;
    int ready = (digitizer & NID_READY) != 0;

    PyDict_SetItemString(result, "has_touch_digitizer", has_touch ? Py_True : Py_False);
    PyDict_SetItemString(result, "digitizer_flags", PyLong_FromLong(digitizer));
    PyDict_SetItemString(result, "max_touch_points", PyLong_FromLong(max_touches));
    PyDict_SetItemString(result, "integrated_touch", integrated ? Py_True : Py_False);
    PyDict_SetItemString(result, "external_touch", external ? Py_True : Py_False);
    PyDict_SetItemString(result, "touch_ready", ready ? Py_True : Py_False);

    /* Try InitializeTouchInjection */
    BOOL init_result = pfnInitializeTouchInjection(1, TOUCH_FEEDBACK_DEFAULT);
    DWORD init_error = init_result ? 0 : GetLastError();

    PyDict_SetItemString(result, "init_works", init_result ? Py_True : Py_False);
    PyDict_SetItemString(result, "init_error", PyLong_FromUnsignedLong(init_error));

    if (!init_result) {
        char diagnosis[256];
        if (init_error == 5) {
            snprintf(diagnosis, sizeof(diagnosis),
                "InitializeTouchInjection failed with ERROR_ACCESS_DENIED (5). "
                "Try running as Administrator.");
        } else if (init_error == 87) {
            snprintf(diagnosis, sizeof(diagnosis),
                "InitializeTouchInjection failed with ERROR_INVALID_PARAMETER (87).");
        } else {
            snprintf(diagnosis, sizeof(diagnosis),
                "InitializeTouchInjection failed with error %lu.", init_error);
        }
        PyDict_SetItemString(result, "inject_works", Py_False);
        PyDict_SetItemString(result, "inject_error", PyLong_FromLong(0));
        PyDict_SetItemString(result, "diagnosis", PyUnicode_FromString(diagnosis));
        return result;
    }

    /* Try InjectTouchInput */
    POINTER_TOUCH_INFO contact;
    memset(&contact, 0, sizeof(POINTER_TOUCH_INFO));

    contact.pointerInfo.pointerType = PT_TOUCH;
    contact.pointerInfo.pointerId = 0;
    contact.pointerInfo.ptPixelLocation.x = 100;
    contact.pointerInfo.ptPixelLocation.y = 100;
    contact.pointerInfo.pointerFlags = POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT;
    contact.touchFlags = TOUCH_FLAG_NONE;
    contact.touchMask = TOUCH_MASK_CONTACTAREA | TOUCH_MASK_ORIENTATION | TOUCH_MASK_PRESSURE;
    contact.orientation = 90;
    contact.pressure = 32000;
    contact.rcContact.left = 98;
    contact.rcContact.right = 102;
    contact.rcContact.top = 98;
    contact.rcContact.bottom = 102;

    BOOL inject_result = pfnInjectTouchInput(1, &contact);
    DWORD inject_error = inject_result ? 0 : GetLastError();

    /* Clean up if DOWN succeeded */
    if (inject_result) {
        contact.pointerInfo.pointerFlags = POINTER_FLAG_UP;
        pfnInjectTouchInput(1, &contact);
    }

    PyDict_SetItemString(result, "inject_works", inject_result ? Py_True : Py_False);
    PyDict_SetItemString(result, "inject_error", PyLong_FromUnsignedLong(inject_error));

    /* Generate diagnosis */
    char diagnosis[512];
    if (inject_result) {
        snprintf(diagnosis, sizeof(diagnosis),
            "Touch injection is fully functional.");
    } else if (inject_error == 5) {
        snprintf(diagnosis, sizeof(diagnosis),
            "InjectTouchInput failed with ERROR_ACCESS_DENIED (5). "
            "Run as Administrator to enable touch injection.");
    } else if (inject_error == 87) {
        if (!has_touch) {
            snprintf(diagnosis, sizeof(diagnosis),
                "InjectTouchInput failed with ERROR_INVALID_PARAMETER (87). "
                "No touch digitizer detected (SM_DIGITIZER=0x%x). "
                "Touch injection likely requires touch hardware.", digitizer);
        } else if (!ready) {
            snprintf(diagnosis, sizeof(diagnosis),
                "InjectTouchInput failed with ERROR_INVALID_PARAMETER (87). "
                "Touch hardware detected but not ready (SM_DIGITIZER=0x%x). "
                "Touch subsystem may need initialization.", digitizer);
        } else {
            snprintf(diagnosis, sizeof(diagnosis),
                "InjectTouchInput failed with ERROR_INVALID_PARAMETER (87). "
                "Touch hardware present and ready, but injection failed. "
                "This may be a driver or permission issue. Try running as Administrator.");
        }
    } else {
        snprintf(diagnosis, sizeof(diagnosis),
            "InjectTouchInput failed with error %lu.", inject_error);
    }

    PyDict_SetItemString(result, "diagnosis", PyUnicode_FromString(diagnosis));

    /* Update module state if injection worked */
    if (inject_result) {
        touch_initialized = 1;
        max_contacts = 1;
    }

    return result;
}

/* Module method table */
static PyMethodDef wintouch_methods[] = {
    {"initialize", (PyCFunction)wintouch_initialize, METH_VARARGS | METH_KEYWORDS,
     "Initialize touch injection (max_contacts=1, feedback_mode=FEEDBACK_DEFAULT)"},
    {"inject", wintouch_inject, METH_VARARGS,
     "Inject touch input events (contacts_list)"},
    {"is_available", wintouch_is_available, METH_NOARGS,
     "Check if touch injection API is available"},
    {"is_initialized", wintouch_is_initialized, METH_NOARGS,
     "Check if touch injection is initialized"},
    {"get_max_contacts", wintouch_get_max_contacts, METH_NOARGS,
     "Get maximum configured simultaneous contacts"},
    {"diagnose", wintouch_diagnose, METH_NOARGS,
     "Diagnose touch injection capability and return detailed status"},
    {NULL, NULL, 0, NULL}
};

/* Module definition */
static struct PyModuleDef wintouch_module = {
    PyModuleDef_HEAD_INIT,
    "_wintouch",
    "Low-level Windows Touch Injection API wrapper",
    -1,
    wintouch_methods
};

/* Module initialization */
PyMODINIT_FUNC PyInit__wintouch(void) {
    PyObject *m;

    m = PyModule_Create(&wintouch_module);
    if (m == NULL) {
        return NULL;
    }

    /* Pointer flags */
    PyModule_AddIntConstant(m, "POINTER_FLAG_NONE", POINTER_FLAG_NONE);
    PyModule_AddIntConstant(m, "POINTER_FLAG_NEW", POINTER_FLAG_NEW);
    PyModule_AddIntConstant(m, "POINTER_FLAG_INRANGE", POINTER_FLAG_INRANGE);
    PyModule_AddIntConstant(m, "POINTER_FLAG_INCONTACT", POINTER_FLAG_INCONTACT);
    PyModule_AddIntConstant(m, "POINTER_FLAG_FIRSTBUTTON", POINTER_FLAG_FIRSTBUTTON);
    PyModule_AddIntConstant(m, "POINTER_FLAG_PRIMARY", POINTER_FLAG_PRIMARY);
    PyModule_AddIntConstant(m, "POINTER_FLAG_CONFIDENCE", POINTER_FLAG_CONFIDENCE);
    PyModule_AddIntConstant(m, "POINTER_FLAG_CANCELED", POINTER_FLAG_CANCELED);
    PyModule_AddIntConstant(m, "POINTER_FLAG_DOWN", POINTER_FLAG_DOWN);
    PyModule_AddIntConstant(m, "POINTER_FLAG_UPDATE", POINTER_FLAG_UPDATE);
    PyModule_AddIntConstant(m, "POINTER_FLAG_UP", POINTER_FLAG_UP);

    /* Touch flags */
    PyModule_AddIntConstant(m, "TOUCH_FLAG_NONE", TOUCH_FLAG_NONE);

    /* Touch mask */
    PyModule_AddIntConstant(m, "TOUCH_MASK_NONE", TOUCH_MASK_NONE);
    PyModule_AddIntConstant(m, "TOUCH_MASK_CONTACTAREA", TOUCH_MASK_CONTACTAREA);
    PyModule_AddIntConstant(m, "TOUCH_MASK_ORIENTATION", TOUCH_MASK_ORIENTATION);
    PyModule_AddIntConstant(m, "TOUCH_MASK_PRESSURE", TOUCH_MASK_PRESSURE);

    /* Feedback modes */
    PyModule_AddIntConstant(m, "FEEDBACK_DEFAULT", TOUCH_FEEDBACK_DEFAULT);
    PyModule_AddIntConstant(m, "FEEDBACK_INDIRECT", TOUCH_FEEDBACK_INDIRECT);
    PyModule_AddIntConstant(m, "FEEDBACK_NONE", TOUCH_FEEDBACK_NONE);

    return m;
}
