GInsapy
=======

Restriction
-----------

GInsapy was developed by Gantner Instruments to illustrate the GInsData API with Python.
Despite our efforts, this software package is delivered "AS IS" without warranty.
Please contact your Gantner Instruments support team for any suggestions.

Package structure
-----------------

.. code-block:: text

    ginsapy/                               # Project directory
      doc/                                 # Sphinx documentation
      src/
        ginsapy/
          examples/
            CustomHelpFormatter.py
            example_buffer_to_csv.py
            example_connect_controller.py
            example_create_buffer.py
            example_create_udbf_file_buffer.py
            example_create_udbf_file_buffer_multiple_files.py
            example_csv_to_buffer.py
            example_get_buffer.py
            example_get_csv.py
            example_microphone.py
            example_read_dat_files.py
            example_websocket_read_buffer.py
            example_websocket_read_info.py
            example_websocket_read_online.py
            example_websocket_write_online.py
            GinsDataloggerReadDatFiles.dat
          giutility/ # Gantner Instruments DLL wrapper to invocate HSP functions


      LICENSE
      README.md
      requirements.txt
      setup.py
      startup.py                           # File to automate installation process

Gantner Instruments DLL
-----------------------
A version of the Gantner Instruments 32/64-bit DLL (giutility.dll) is **NOT** included in the package. The giutility.dll can be found in the installation folder of GI.bench.

License
-------
This software package is delivered under MIT license.

License disclaimer
------------------

Copyright (c) 2020 Gantner Instruments

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
