Firefly Scientific Data Server
==============================

Firefly is a platform that enables data in the IRIG106 (ch10) telemetry standard to be converted to the HDF5 format and made available for query and analysis using JupyterLab notebooks.

Using Firefly with HDF KitaLab
------------------------------

Firefly has been setup on AWS and can be access via the Kita Lab shared environment. Using Kita Lab you can access a large collection of ch10 data and run sample notebooks that illustrate how to use the Firefly tools to search and analyze the data collection.

To access follow these steps:

1. Go to this page: <https://www.hdfgroup.org/hdfkitalab/> to register for a Kita Lab account
2. Sign into Kita Lab (<https://hdflab.hdfgroup.org>) using your account credentials
3. Once signed in, open a terminal ("File|New Launcher", select "Terminal") and clone the repo: `$ git clone https://github.com/AkadioInc/firefly`
4. Also from the terminal, you can run queries such as those given in (docs/Firefly_domain_query_examples.md) and see listings of HSDS files that meet the given criteria
5. In the JupyterLab browser, select firefly/notebooks/FlightCollection.ipynb or firefly/notebooks/FlightSegment.ipynb, and step through the examples of using the Firefly Python package.  If you are new to JupyterLab, this is a good guide: <https://www.dataquest.io/blog/jupyter-notebook-tutorial/>
6. The Firefly browser is avaible from "Experimental/FIREfly Browser". Use the query widget to set attributes and see the resulting list of files that meet the given contstraints


Installation
------------

Firefly has been setup on AWS and can be access via the Kitalab shared environment (see <https://www.hdfgroup.org/hdfkitalab/>).  Firefly can be installed with other cloud providers or in an on-prem datacenter, but this has not been verified.

Prequisites for FireFly are JupyterLab on a Kubernetes cluster and HSDS (Highly Scalable Data Server).  See: <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html> for steps to setup Kubernetes and the JupyterLab environment.

Install HSDS on the same Kubernetes cluster that was used for JupyterLab.  See: <https://github.com/HDFGroup/hsds/blob/master/docs/kubernetes_install.md> for installation instructions.

Next install the Kubernetes apps: ch10convert and ch10watchdog using the yaml files [ch10convert.yml](k8s_apps/ch10convert/ch10convert.yml) and [ch10watchdog.yaml](k8s_apps/ch10watchdog/ch10watchdog.yml).

Finally install the JupyterLab extensions as described in [firefly-extension/README.md](jupyterlab/firefly-extension/README.md)
