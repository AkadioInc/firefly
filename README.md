Firefly Scientific Data Server
==============================

Firefly is a platform that enables data in the IRIG106 telemetry standard to be converted to the HDF5 format available for query and analysis using JupyterLab notebooks.

Installation
------------

Firefly has been setup on AWS and can be access via the Kitalab shared environment (see <https//www.hdfgroup.org/hdfkitalab.html>).  Firefly can be installed with other cloud providers or in an on-prem datacenter, but this has not been verified.

Prequisites for FireFly are JupyterLab on a Kubernetes cluster and HSDS (Highly Scalable Data Server).  See: <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html> for steps to setup Kubernetes and the JupyterLab environment.

Install HSDS on the same Kubernetes cluster that was used for JupyterLab.  See: <https://github.com/HDFGroup/hsds/blob/master/docs/kubernetes_install.md> for installation instructions.

Next install the Kubernetes apps: ch10convert and ch10watchdog using the yaml files (k8s_apps/ch10convert/ch10convert.yml) and (k8s_apps/ch10watchdog/ch10watchdog.yml).

Finally install the JupyterLab extensions as described in (jupyterlab/firefly-extension/README.md)
