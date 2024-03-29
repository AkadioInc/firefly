FIREfly Scientific Data Server
==============================

FIREfly is a platform that enables data in the IRIG106 (ch10) telemetry standard to be converted to the HDF5 format and made available for query and analysis using JupyterLab notebooks.

Using FIREfly with HDF KitaLab
------------------------------

FIREfly has been setup on AWS and can be access via the Kita Lab shared environment. Using Kita Lab you can access a large collection of ch10 data and run sample notebooks that illustrate how to use the FIREfly tools to search and analyze the data collection.

To access follow these steps:

1. Go to this page: <https://www.hdfgroup.org/hdfkitalab/> to register for a Kita Lab account
2. Sign into Kita Lab (<https://hdflab.hdfgroup.org>) using your account credentials
3. Once signed in, open a terminal ("File|New Launcher", select "Terminal") and clone the repo: `$ git clone https://github.com/AkadioInc/firefly`
4. Also from the terminal, you can run queries such as those given in (docs/Firefly_domain_query_examples.md) and see listings of HSDS files that meet the given criteria
5. In the JupyterLab browser, select firefly/notebooks/FlightCollection.ipynb or firefly/notebooks/FlightSegment.ipynb, and step through the examples of using the FIREfly Python package.  If you are new to JupyterLab, this is a good guide: <https://www.dataquest.io/blog/jupyter-notebook-tutorial/>
6. The FIREfly browser is avaible from "Experimental/FIREfly Browser". Use the query widget to set attributes and see the resulting list of files that meet the given contstraints


Installation
------------

AWS offers the easiest environment for installing FIREfly. It can be installed with other cloud providers or in an on-prem datacenter, but this has not been verified.

Prequisites for FireFly are JupyterLab on a Kubernetes cluster and HSDS (Highly Scalable Data Server).  See: <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html> for steps to setup Kubernetes and the JupyterLab environment.

Install HSDS on the same Kubernetes cluster that was used for JupyterLab.  See: <https://github.com/HDFGroup/hsds/blob/master/docs/kubernetes_install.md> for installation instructions.

Next install the Kubernetes apps: ch10convert and ch10watchdog using the yaml files [ch10convert.yml](k8s_apps/ch10convert/ch10convert.yml) and [ch10watchdog.yaml](k8s_apps/ch10watchdog/ch10watchdog.yml).

Finally, install the JupyterLab extensions as described in [firefly-extension/README.md](jupyterlab/firefly-extension/README.md)

Repository Content
------------------

The following outlines what's available in this repository:

* [Docker](docker/README.md): Docker files for creating docker images with the requiste tools
* [docs](docs/FIREFly_HDF5_Format.md): FIREfly format and related documentation
* [filefly](firefly): The FIREfly Python package source files
* [firefly-extension/README.md](jupyterlab/firefly-extension/README.md): FIREfly JupyterLab extension
* [k8s_apps/admin](k8s_apps/admin): Admin scripts for Kubernetes
* [k8s_apps/ch10convert](k8s_apps/ch10convert): Kubernetes app for ch10 to hdf5 conversion
* [k8s_apps/ch10wathdog](k8s_apps/ch10watchdog): Kubernetes app to monitor ch10 source files
* [k8s_apps/ch10gen](k8s_apps/ch10gen): Kubernetes app to generate synthetic ch10 files
* [notebooks](notebooks): Sample Python notebooks
* [scripts](scripts): Python scripts for ch10 conversion, summarizing content, and adding EU data.


Related Projects
----------------

The following projects are utilized in FIREfly:

* HSDS: <https://github.com/HDFGroup/hsds>
* h5pyd: <https://github.com/HDFGroup/h5pyd>
* IRIG106: <https://github.com/bbaggerman/irig106lib>

Other useful resources
----------------------

* SciPy17 on HSDS Presentation: <http://s3.amazonaws.com/hdfgroup/docs/hdf_data_services_scipy2017.pdf>
* HDF5 For the Web: <https://hdfgroup.org/wp/2015/04/hdf5-for-the-web-hdf-server>
* HSDS Security: <https://hdfgroup.org/wp/2015/12/serve-protect-web-security-hdf5>
* HSDS with Jupyter: <https://www.slideshare.net/HDFEOS/hdf-kita-lab-jupyterlab-hdf-service>
* Kubernetes documentation: <https://kubernetes.io/docs/home/>
* JupyterHub documentation: <https://jupyterhub.readthedocs.io/en/stable/>
* JupyterLab documentation: <https://jupyterlab.readthedocs.io/en/stable/>