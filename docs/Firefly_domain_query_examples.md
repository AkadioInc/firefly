# HSDS REST Requests for domain queries

The following are some sample curl requests that illustrate how to use the HSDS Rest API to list domains meeting certain conditions.

* List all domains in the FIREfly HDF folder
  * cli: `hsls /FIREfly/h5/ --bucket firefly-hsds`
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/domains" --data-urlencode "domain=/FIREfly/h5/" --data-urlencode "bucket=firefly-hsds"`

* List first 10 domains in FIREfly HDF folder
  * cli: `hsls /FIREfly/h5/ --bucket firefly-hsds | head`
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/domains" --data-urlencode "domain=/FIREfly/h5/" --data-urlencode "bucket=firefly-hsds" --data-urlencode "Limit=10"`

* List next domains after domain /FIREfly/h5/A10-C-ED060004-201212270208.h5
  * cli: tbd
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/domains" --data-urlencode "domain=/FIREfly/h5/" --data-urlencode "bucket=firefly-hsds" --data-urlencode "Limit=10" --data-urlencode "Marker=/FIREfly/h5/A10-C-ED060004-201212270208.h5"`

* List domains with aircraft type A10

  * cli: `hsls --bucket firefly-hsds --query "aircraft_type == 'A10'"  /FIREfly/h5/`
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/domains" --data-urlencode "domain=/FIREfly/h5/" --data-urlencode "bucket=firefly-hsds" --data-urlencode "query=aircraft_type == 'A10'"`

* List flights with start times between 2005-06-01 and 2005-07-01

  * cli:  `hsls --bucket firefly-hsds --query "time_coverage_start > '2005-06-01' AND time_coverage_start < '2005-07-01'"  /FIREfly/h5/`
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/domains" --data-urlencode "domain=/FIREfly/h5/" --data-urlencode "bucket=firefly-hsds" --data-urlencode "query=time_coverage_start > '2005-06-01' AND time_coverage_start < '2005-07-01'"`

* Get attributes for particular domain

  * cli: `hsls /FIREfly/h5/T-38-ED070987-200605020938.h5 --showattrs --bucket firefly-hsds`
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/groups/g-7926cbd7-c22a1918-f1ae-435f4a-a29190/attributes" --data-urlencode "domain=/FIREfly/h5/T-38-ED070987-200605020938.h5" --data-urlencode "bucket=firefly-hsds"`

* Get given attribute for domain

  * cli: N/A
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/groups/g-7926cbd7-c22a1918-f1ae-435f4a-a29190/attributes/takeoff_location" --data-urlencode "domain=/FIREfly/h5/T-38-ED070987-200605020938.h5" --data-urlencode "bucket=firefly-hsds"`

* Get all metadata for a particular domain
  * cli: `hsls /FIREfly/h5/T-38-ED070987-200605020938.h5 --showattrs --bucket firefly-hsds`
  * rest: `curl -G "http://hsdshdflab.hdfgroup.org/groups/g-7926cbd7-c22a1918-f1ae-435f4a-a29190" --data-urlencode ""include_attrs=1" --data-urlencode "domain=/FIREfly/h5/T-38-ED070987-200605020938.h5" --data-urlencode "bucket=firefly-hsds"`