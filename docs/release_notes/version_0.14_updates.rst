Version 0.14 Updates
/////////////////////////

Version 0.14.0
===============

SYNOP and TEMP readers
---------------------------

- Updated the list of keys used to generate the ``stnid`` parameter in the :ref:`synop <synop-reader>` and :ref:`temp <temp-reader>` readers. (:pr:`99`). To determine ``stnid`` the following keys are tried in order. The major change is the ``ident`` key (only available for messages generated/archived at ECMWF), which is now always tried first:

    - "ident"
    - :ref:`WMO station id <key-wmo-station-id>`
    - :ref:`WIGOS station id <key-WIGOS-station-id>`
    - "shipOrMobileLandStationIdentifier"
    - "station_id"
    - "icaoLocationIndicator"
    - "stationOrSiteName"
    - "longStationName"


- Added the ``stnid_key`` parameter to the :ref:`synop <synop-reader>` and :ref:`temp <temp-reader>` readers to specify a user-defined list of keys to generate the ``stnid`` parameter. (:pr:`99`)
- Ensured that the ``stnid`` parameter is always a string or None. (:pr:`99`)
- Enured that if any component in :ref:`WMO station id <key-wmo-station-id>` is missing the whole :ref:`WMO station id <key-wmo-station-id>` is regarded as missing when generating the ``stnid`` parameter. (:pr:`99`)
- Renamed the parameter "wgust" to "max_wgust" in the :ref:`synop reader <synop-reader>` (:pr:`95`). The windgust parameter names are as follows:

    max_wgust
    max_wgust_speed
    max_wgust_dir
