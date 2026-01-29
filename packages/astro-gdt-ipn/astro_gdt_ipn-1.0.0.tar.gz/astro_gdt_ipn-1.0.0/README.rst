IPN Gamma-ray Localization Toolkit
========================

Installation
============

..  Note:: Requires: Python >=3.11


How to Install
--------------

.. Note::
    This will need to be updated for release, but for now, these are instructions
    on how to install locally so that you can edit and develop.

To install via ``pip``, navigate to the directory where you want the virtual
environment to live and::
    
    $ python3 -m venv ipn-env
    $ source ipn/bin/activate
    
This will create a new virtual environment called "ipn-env" and activates the 
environment.

To install via ``conda``:: 
    
    $ conda create --name ipn-env
    $ source activate ipn-env

It's also good to ensure you have ``pip`` updated::
    
    $ pip3 install --upgrade pip

Then you can install the toolkit::
    
    $ pip3 install -e <path_to_toolkit>/gdt-ipn/
    $ pip3 install ipython

Note the ``-e`` flag on the install, which allows the package to be editable. 

If you don't wish to install via a virtual environment, you are welcome to 
install with your preferred method, but you may encounter more difficulties, 
especially if you have existing package installs that conflict with what is 
required for the Data Tools.  Check the requirements.txt for required packages 
and versions.

----

How to Uninstall
----------------

To uninstall::

    $ pip3 uninstall ipn

----

Quickstart
----------
To load the toolkit within your python environment, simply::
    
    import ipn

The annulus module can be accessed by::

    from ipn import annulus
    
----

Running Unit Tests
------------------
In the gdt-ipn root directory, run::
    
    $ python3 -m unittest test.test_grb

This will run the unit test for the ``Grb``` class I've added to the main package.
Other unit tests should follow the general procedure in test/test_grb.py


Known Issues
------------
