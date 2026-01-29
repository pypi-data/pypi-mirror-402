==================================================================
bisos.tocsModules: Target Oriented Command-Services (tocs) Modules
==================================================================

.. contents::
   :depth: 3
..

Overview
========

*bisos.tocsModules* provides general facilities for creation of arget
Oriented Command-Services (tocs) Modules.

In this model Targets are collections of accessible Managed Objects
(MOs). Target-Modules are Python modules which are aware of the Target's
set of MOs

bisos.tocsModules is a python package that uses the
`PyCS-Framework <https://github.com/bisos-pip/pycs>`__.

.. _table-of-contents:

Table of Contents TOC
=====================

-  `Overview <#overview>`__
-  `The model and terminology of Modules, Targets and Managed
   Objects <#the-model-and-terminology--of-modules-targets-and-managed-objects>`__
-  `Part of BISOS — ByStar Internet Services Operating
   System <#part-of-bisos-----bystar-internet-services-operating-system>`__
-  `Target Awareness of
   Target-Modules <#target-awareness-of-target-modules>`__
-  `Installation <#installation>`__

   -  `Installation With pip <#installation-with-pip>`__
   -  `Installation With pipx <#installation-with-pipx>`__
   -  `Post Installation Basic
      Testing <#post-installation-basic-testing>`__

-  `Usage <#usage>`__

   -  `Local Usage (system
      command-line) <#local-usage-system-command-line>`__

-  `Documentation and Blee-Panels <#documentation-and-blee-panels>`__

   -  `bisos.tocsModules Blee-Panels <#bisostocsmodules-blee-panels>`__

-  `Support <#support>`__
-  `Planned Improvements <#planned-improvements>`__

The model and terminology of Modules, Targets and Managed Objects
=================================================================

`The model of terminology of
TocsModules <https://www.puppet.com/docs/puppet/7/facter.html>`__ is
precise and well defined.

Here is a summary of the key concepts and where appropriate their
origins:

-  System: as defined in ISO-7498 (X.200)
   [[file:./panels/bisos.tocsModules/model/X.200.pdf
-  Managed Object: as defined in X.700
   `file:./panels/bisos.tocsModules/model/X.700.pdf <./panels/bisos.tocsModules/model/X.700.pdf>`__
-  Managed Object Parameter: as defined in X.720
   `file:./panels/bisos.tocsModules/model/X.720.pdf <./panels/bisos.tocsModules/model/X.720.pdf>`__
-  Target: An entity within a system containing one or more Managed
   Objects.
-  Cluster: A system containing one or more Targets
-  Pack: A named list of Clusters
-  Target-Module: A python module capable of processing specific type of
   targets. Modules can be of different types such as those enumerated
   below.
-  BISOS-CS-Module: A Native CS module that is aware of targets.
-  Uploadable-Modules: Modules that can be uploaded into the PyCS
   targets environment. This is accomplished through the
   bisos.uploadAsCs package.
-  Run Disposition. Based on a the CS Parameter –runDisposition, the
   list of Packs/Clusters/Targets can be invoked sequentially or in
   parallel

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
  Polyexistentials <https://github.com/bxplpc/120033>`__.
  *bisos.tocsModules* is part of BISOS.

Target Awareness of Target-Modules
==================================

*bisos.tocsModules* provides various facilities to Target-Modules.

By importing py3/bisos/tocsModules/facterModule\ :sub:`csu`.py the
following parameters are defined:

–targetsFile

–targetsNu

–clustersList

–packs

–runDisposition

Installation
============

The sources for the bisos.tocsModules pip package are maintained at:
https://github.com/bisos-pip/tocsModules.

The bisos.tocsModules pip package is available at PYPI as
https://pypi.org/project/bisos.tocsModules

You can install bisos.tocsModules with pip or pipx.

Installation With pip
---------------------

If you need access to bisos.tocsModules as a python module, you can
install it with pip:

.. code:: bash

   pip install bisos.tocsModules

Installation With pipx
----------------------

If you only need access to bisos.tocsModules on command-line, you can
install it with pipx:

.. code:: bash

   pipx install bisos.tocsModules

Post Installation Basic Testing
-------------------------------

After the installation, run some basic tests:

.. code:: bash

   tocsModules.cs
   tocsModules networking.interfaces.lo.bindings

Usage
=====

Local Usage (system command-line)
---------------------------------

``tocsModules.cs`` does the equivalent of tocsModules.

.. code:: bash

   bin/tocsModules.cs

Documentation and Blee-Panels
=============================

bisos.tocsModules is part of ByStar Digital Ecosystem
http://www.by-star.net.

This module's primary documentation is in the form of Blee-Panels.
Additional information is also available in:
http://www.by-star.net/PLPC/180047

bisos.tocsModules Blee-Panels
-----------------------------

bisos.tocsModules Blee-Panles are in ./panels directory. From within
Blee and BISOS these panles are accessible under the Blee "Panels" menu.

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

-  Enumerate applicabilities: telecom/SON, datacenter, CMIP-MOs
-  py3/bisos/tocsModules/tocsModule\ :sub:`csu`.py
