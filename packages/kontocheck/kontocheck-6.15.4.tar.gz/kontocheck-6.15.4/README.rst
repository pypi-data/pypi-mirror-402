kontocheck
==========

Python ctypes wrapper of the konto_check library.

This module is based on konto_check_, a small library to check German
bank accounts. It implements all check methods and IBAN generation
rules, published by the German Central Bank.

In addition it provides access to the SCL Directory and the possibility
to verify VAT-IDs by the German Federal Central Tax Office.

.. _konto_check: http://kontocheck.sourceforge.net


Example
-------

.. sourcecode:: python
    
    import kontocheck
    kontocheck.lut_load()
    bankname = kontocheck.get_name('37040044')
    iban = kontocheck.create_iban('37040044', '532013000')
    kontocheck.check_iban(iban)
    bic = kontocheck.get_bic(iban)
    bankname = kontocheck.scl_get_bankname('VBOEATWW')


Changelog
---------

v6.15.4
    - Fixed eu_check_vatid()
    - Updated the LUT data file

v6.15.3
    - Updated the LUT data file

v6.15.2
    - Updated the LUT data file

v6.15.1
    - Updated the LUT data file

v6.15.0
    - Updated the konto_check library to version 6.15
    - Updated the LUT data file

v6.14.2
    - Updated the LUT data file

v6.14.1
    - Updated the LUT data file

v6.14.0
    - Updated the konto_check library to version 6.14
    - Updated the LUT data file

v6.13.2
    - Added VAT-ID check of the European Commission

v6.13.1
    - Updated the konto_check library to version 6.13
    - Now uses the SCL Directory implemented in konto_check.
    - Updated the LUT data file

v6.11.2
    - Updated the LUT data file
    - Updated the SCL Directory

v6.11.1
    - Updated the LUT data file
    - Updated the SCL Directory

v6.11.0
    - Updated the konto_check library to version 6.11
    - Updated the LUT data file
    - Updated the SCL Directory
    - Fixed minor bug in *get_bic* when called with bankcodes.

v6.10.0
    - Updated the konto_check library to version 6.10
    - Updated the LUT data file
    - Updated the SCL Directory
    - Fixed bug of *check_iban* running into a segfault with long account numbers.
    - Made *get_bic* to accept bankcodes in addition to IBANs.

v6.08.1
    - Updated the LUT data file

v6.08.0
    - Updated the konto_check library to version 6.08
    - Updated the LUT data file
    - Updated the SCL Directory

v6.05.0
    - Updated the konto_check library to version 6.05
    - Updated the LUT data file
    - Updated the SCL Directory

v6.02.0
    - Updated the konto_check library to version 6.02
    - Updated the LUT data file
    - Updated the SCL Directory

v6.01.0
    - Updated the konto_check library to version 6.01
    - Updated the LUT data file
    - Updated the SCL Directory
    - Replaced SCL Sqlite database with plain CSV file

v5.10.0
    - Updated the konto_check library to version 5.10
    - Updated the LUT data file
    - Updated the SCL Directory

v5.9.0
    - Updated the konto_check library to version 5.9
    - Updated the LUT data file
    - Updated the SCL Directory

v5.8.2
    - Updated the LUT data file
    - Updated the SCL Directory

v5.8.1
    - Updated the LUT data file
    - Updated the SCL Directory

v5.8.0
    - Updated the konto_check library to version 5.8
    - Updated the LUT data file
    - Updated the SCL Directory

v5.7.0
    - Updated the konto_check library to version 5.7
    - Updated the SCL Directory

v5.5.11
    - Updated the LUT data file
    - Updated the SCL Directory

v5.5.10
    - Made the package Py2/3 compatible.
    - Now textual return values are always unicode strings.

v5.5.6
    - Bug fix querying the SCL Directory

v5.5.5
    - Updated the LUT data file
    - Updated the SCL Directory

v5.5.4
    - Fixed a bug in setup.py

v5.5.3
    - Normalized BIC in scl_* functions

v5.5.2
    - Added the SCL Directory, published by the German Central Bank
    - Added some functions to query the SCL Directory.
    - Added functionality to check VAT-IDs for validity.

v5.5.1
    - Minor bug fixes
    
v5.5.0
    - Updated the konto_check library to version 5.5
    - Fixed a bug on Windows using the wrong MSVCRT version.

v5.4.2
    - Updated the LUT data file since it contained an invalid BIC

v5.4.1
    - Fixed a bug on Windows systems, failed to load msvcrt

v5.4.0
    - Updated the konto_check library to version 5.4

v5.3.0
    - Updated the konto_check library to version 5.3
    - Fixed a bug in function get_name that did not recognize an IBAN.

v5.2.1
    - Replaced Cython with ctypes, since it is easier to maintain for different plattforms.
