Yoctopuce Typed Python library (BETA)
=====================================



## Content of this package

* Documentation/

		API Reference, in HTMLformat

* Examples/

		Directory with sample programs in Python

* yoctolib/

		Source code of the library, entirely written in Python

* FILES.txt

		List of files contained in this archive

* RELEASE.txt

		Release notes

## Using the local copy of the library

The examples in directory Examples refer to the library as ``yoctolib.yocto_xxxx``.
In order to allow your Python environment to locate the library in this directory 
rather than having to install it from PyPI, run the following command in *this* directory:
````
pip install -e .
````
This will result in linking in your *local packages* this local copy of the library.
To undo this operation, simply run
````
pip uninstall yoctolib
````

## Using PyPI package

This source code is also published on PyPI (the Python Package Index)
https://pypi.python.org/pypi/yoctolib

To install it from PyPI, simply run the pip install command like this
````
pip install yoctolib
````

If you already have the library installed from PyPI you can upgrade it with the following command:
````
pip install -U yoctolib
````


## More help

For more details, refer to the documentation specific to each product, which
includes sample code with explanations, and a programming reference manual.
In case of trouble, contact support@yoctopuce.com

Have fun !

## License information

Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.

Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
non-exclusive license to use, modify, copy and integrate this
file into your software for the sole purpose of interfacing
with Yoctopuce products.

You may reproduce and distribute copies of this file in
source or object form, as long as the sole purpose of this
code is to interface with Yoctopuce products. You must retain
this notice in the distributed source file.

You should refer to Yoctopuce General Terms and Conditions
for additional information regarding your rights and
obligations.

THE SOFTWARE AND DOCUMENTATION ARE PROVIDED "AS IS" WITHOUT
WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR
SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT
LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
WARRANTY, OR OTHERWISE.
