=================================================================================
bisos.facter: Adoption and adaptation of facter to Python and as Command-Services
=================================================================================

.. contents::
   :depth: 3
..

Overview
========

*bisos.facter* provides access to facter information through python.

bisos.facter is a python package that uses the
`PyCS-Framework <https://github.com/bisos-pip/pycs>`__ for adoption and
adaptation of **facter** to python and PyCS-Framework. It is a
BISOS-Capability and a Standalone-BISOS-Package.

*bisos.facter* is based on the
`PyCS-Foundation <https://github.com/bisos-pip/b>`__ and can be used
both as a Command and as a Service (invoke/perform model of remote
operations using `RPyC <https://github.com/tomerfiliba-org/rpyc>`__).
Use of bisos.facter as a service, can facilitate central management of
multiple systems.

Package Documentation At Github
===============================

The information below is a subset of the full of documentation for this
bisos-pip package. More complete documentation is available at:
https://github.com/bisos-pip/capability-cs

.. _table-of-contents:

Table of Contents TOC
=====================

-  `Overview <#overview>`__
-  `Package Documentation At
   Github <#package-documentation-at-github>`__
-  `About facter <#about-facter>`__
-  `Part of BISOS — ByStar Internet Services Operating
   System <#part-of-bisos-----bystar-internet-services-operating-system>`__
-  `bisos.facter is a Command-Services PyCS
   Facility <#bisosfacter-is-a-command-services-pycs-facility>`__
-  `bisos.facter as a Standalone Piece of
   BISOS <#bisosfacter-as-a-standalone-piece-of-bisos>`__
-  `Installation <#installation>`__

   -  `Installation With pip <#installation-with-pip>`__
   -  `Installation With pipx <#installation-with-pipx>`__
   -  `Post Installation Basic
      Testing <#post-installation-basic-testing>`__

-  `Usage <#usage>`__

   -  `Local Usage (system
      command-line) <#local-usage-system-command-line>`__
   -  `Remote Usage (as a service –
      Performer+Invoker) <#remote-usage-as-a-service----performerinvoker>`__

      -  `Performer <#performer>`__
      -  `Invoker <#invoker>`__

   -  `Use by python script <#use-by-python-script>`__

-  `bisos.facter as an Example of Command Services (PyCS) – Code
   Walkthrough <#bisosfacter-as-an-example-of-command-services-pycs----code-walkthrough>`__

   -  `./bin/facter.cs (./bin/facter-roPerf.cs
      ./bin/facter-roInv.cs) <#py3binfactercs--binfacter-roperfcs--binfacter-roinvcs>`__
   -  `./bisos/facter/facter.py (COMEEGA
      Python) <#py3bisosfacterfacterpy-comeega-python>`__
   -  `./bisos/facter/facter\ conv.py (Conventional
      Python) <#py3bisosfacterfacter_convpy-conventional-python>`__
   -  `./bisos/facter/facter\ csu.py <#py3bisosfacterfacter_csupy>`__
   -  `PyPi and Github Packaging <#pypi-and-github-packaging>`__

-  `Documentation and Blee-Panels <#documentation-and-blee-panels>`__

   -  `bisos.facter Blee-Panels <#bisosfacter-blee-panels>`__

-  `Support <#support>`__
-  `Planned Improvements <#planned-improvements>`__

About facter
============

`Facter <https://www.puppet.com/docs/puppet/7/facter.html>`__ is part of
`puppet <https://www.puppet.com/>`__, but it can also be used without
puppet. Facter gathers information about the system as sets of
hierarchical variables.

To install facter:

.. code:: bash

   sudo apt-get install -y facter

Facter is a ruby package. This bisos.facter python package provides
access to facter information through python both locally and remotely.

Part of BISOS — ByStar Internet Services Operating System
=========================================================

| Layered on top of Debian, **BISOS**: (By\* Internet Services Operating
  System) is a unified and universal framework for developing both
  internet services and software-service continuums that use internet
  services. See `Bootstrapping ByStar, BISOS and
  Blee <https://github.com/bxGenesis/start>`__ for information about
  getting started with BISOS.
| **BISOS** is a foundation for **The Libre-Halaal ByStar Digital
  Ecosystem** which is described as a cure for losses of autonomy and
  privacy in a book titled: `Nature of
  Polyexistentials <https://github.com/bxplpc/120033>`__

*bisos.facter* is part of BISOS. Within BISOS, bisos.cmdb uses
bisos.facter for Configuration Management DataBase purposes.

bisos.facter is a Command-Services PyCS Facility
================================================

bisos.facter can be used locally on command-line or remotely as a
service. bisos.facter is a PyCS multi-unit command-service. PyCS is a
framework that converges development of CLI and Services. PyCS is an
alternative to FastAPI, Typer and Click.

bisos.facter uses the PyCS-Framework to:

#. Provide access to facter facilities through native python.
#. Provide local access to facter facilities on CLI.
#. Provide remote access to facter facilities through remote invocation
   of python Expectation Complete Operations using
   `rpyc <https://github.com/tomerfiliba-org/rpyc>`__.
#. Provide remote access to facter facilities on CLI.

What is unique in the PyCS-Framework is that these four models are all a
single abstraction.

The core of PyCS-Framework is the *bisos.b* package (the
PyCS-Foundation). See https://github.com/bisos-pip/b for an overview.

bisos.facter as a Standalone Piece of BISOS
===========================================

bisos.facter is a standalone piece of BISOS. It can be used as a
self-contained Python package separate from BISOS. Follow the
installation and usage instructions below for your own use.

Installation
============

The sources for the bisos.facter pip package are maintained at:
https://github.com/bisos-pip/facter.

The bisos.facter pip package is available at PYPI as
https://pypi.org/project/bisos.facter

You can install bisos.facter with pip or pipx.

Installation With pip
---------------------

If you need access to bisos.facter as a python module, you can install
it with pip:

.. code:: bash

   pip install bisos.facter

Installation With pipx
----------------------

If you only need access to bisos.facter on command-line, you can install
it with pipx:

.. code:: bash

   pipx install bisos.facter

The following commands are made available:

-  facter.cs
-  facter-roInv.cs
-  facter-roPerf.cs

These are all one file with 3 names. *facter-roInv.cs* and
*facter-roPerf.cs* are sym-links to *facter.cs*

Post Installation Basic Testing
-------------------------------

After the installation, run some basic tests:

.. code:: bash

   facter.cs
   facter networking.interfaces.lo.bindings

Usage
=====

Local Usage (system command-line)
---------------------------------

``facter.cs`` does the equivalent of facter.

.. code:: bash

   bin/facter.cs

Remote Usage (as a service – Performer+Invoker)
-----------------------------------------------

You can also run:

Performer
~~~~~~~~~

Invoke performer as:

.. code:: bash

   bin/facter-roPerf.cs

Invoker
~~~~~~~

.. code:: bash

   bin/facter-roInv.cs

Use by python script
--------------------

bisos.facter Source Code is in written in COMEEGA (Collaborative
Org-Mode Enhanced Emacs Generalized Authorship) –
https://github.com/bx-blee/comeega.

The primary API for bisos.facter is
`file:./bisos/facter/facter_csu.py <./bisos/facter/facter_csu.py>`__. It
is self documented in COMEEGA.

bisos.facter as an Example of Command Services (PyCS) – Code Walkthrough
========================================================================

An overview of the relevant files of the bisos.facter package is
provided below.

./bin/facter.cs (./bin/facter-roPerf.cs ./bin/facter-roInv.cs)
--------------------------------------------------------------

The file `file:./bin/facter.cs <./bin/facter.cs>`__ is a CS-MU
(Command-Services Multi-Unit). It is fundamentally a boiler plate that
has the main framework org-mode Dynamic Block and which imports its
commands from bisos.facter.facter\ :sub:`csu` and
bisos.banna.bannaPortNu modules.

./bisos/facter/facter.py (COMEEGA Python)
-----------------------------------------

The file `file:./bisos/facter/facter.py <./bisos/facter/facter.py>`__
includes functions that run a sub-process with "facter –json", obtain
the json result as a collection of namedtuples. This can then be
subjected to caching and then retrieved based on string representations
mapping to namedtuples.

./bisos/facter/facter\ :sub:`conv`.py (Conventional Python)
-----------------------------------------------------------

The file
`file:./bisos/facter/facter_conv.py <./bisos/facter/facter_conv.py>`__
is same as `file:./bisos/facter/facter.py <./bisos/facter/facter.py>`__
without use of COMEEGA. Without Emacs, it is not easy to read the
COMEEGA files and some people prefer not to use or know about COMEEGA.
In such situations facter\ :sub:`conv`.py can be considered as
conventional sample code.

./bisos/facter/facter\ :sub:`csu`.py
------------------------------------

The file
`file:./bisos/facter/facter_csu.py <./bisos/facter/facter_csu.py>`__ is
a CS-U (Command-Services Unit). It includes definitions of commands and
their CLI params and args.

Implementation of commands in facter\ :sub:`csu`.py rely on facilities
provided in facter.py.

PyPi and Github Packaging
-------------------------

All bisos-pip repos in the https://github.com/bisos-pip github
organization follow the same structure. They all have
`file:./setup.py <./setup.py>`__ files that are driven by
`file:./pypiProc.sh <./pypiProc.sh>`__.

The `file:./setup.py <./setup.py>`__ file is a series of consistent
org-mode Dynamic Block that automatically determine the module name and
the installed and pypi revisions.

The `file:./pypiProc.sh <./pypiProc.sh>`__ uses setup.py and pushes to
pypi when desired and allows for isolated testing using pipx.

Documentation and Blee-Panels
=============================

bisos.facter is part of ByStar Digital Ecosystem http://www.by-star.net.

This module's primary documentation is in the form of Blee-Panels.
Additional information is also available in:
http://www.by-star.net/PLPC/180047

bisos.facter Blee-Panels
------------------------

bisos.facter Blee-Panles are in ./panels directory. From within Blee and
BISOS these panles are accessible under the Blee "Panels" menu.

See
`file:./panels/_nodeBase_/fullUsagePanel-en.org <./panels/_nodeBase_/fullUsagePanel-en.org>`__
for a starting point.

Support
=======

| For support, criticism, comments and questions; please contact the
  author/maintainer
| `Mohsen Banan <http://mohsen.1.banan.byname.net>`__ at:
  http://mohsen.1.banan.byname.net/contact

Planned Improvements
====================

One material use of bisos.facter is to facilitate developement of an
automated Configuration Management DataBase (CMDB) as a centralized
facility that organizes information about system, including the
relationships between hardware, software, and networks. On a per-system
base, bisos.facter can obtain much of that information and through PyCS
it can deliver that information remotely to centralized CMDBs. In this
context CMDBs generally function as invokers and we need to facilitate
ever present bisos.facter performers.

The CMDB invoker part is implemented as bisos.cmdb.

Each BISOS platform needs to run an instance under systemd. I have done
something similar to this for bisos.marmee. That piece need to be
absorbed.
