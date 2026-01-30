Yoctopuce library for Python
============================

This is Yoctopuce Python API. All required source files
are in the Yoctopuce folder. You  will find some small examples
for every available Yoctopuce product in examples folder. The
complete documentation is in the Documentation folder. The
HTML documentation is interactive, similar to JavaDoc


## Content of this package

* Documentation/

		API Reference, in HTML and PDF format

* Examples/

		Directory with sample programs in Python

* yoctopuce/

		Source code of the high-level library (in Python)

* yoctopuce/cdll/

		Low-level library (C source code with makefile
        to build this library is available in the C++ library)

* FILES.txt

		List of files contained in this archive


## PyPI package

There is a small difference between this library and the
the one you can download directly from Yoctopuce, with this
one includes are done the following way:

````
from yoctopuce.yocto_api import *
````
instead of:

````
from yocto_api import *
````

This API uses precompiled C LIB files, sources are located C++ API, available
from Yoctopuce's web site.


## More help

For more details, refer to the documentation specific to each product, which
includes sample code with explanations, and a programming reference manual.
In case of trouble, contact support@yoctopuce.com

Have fun !

