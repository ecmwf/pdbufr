
Version 0.12 Updates
/////////////////////////


Version 0.12.2
===============

- implemented the ``WIGOS_station_id`` computed key for the `WIGOS station identifier <https://community.wmo.int/en/activity-areas/WIGOS/implementation-WIGOS/FAQ-WSI>`_. See details :ref:`here <key-wigos-station-id>`.
- fixed issue when the ``filters`` was not applied if it contained a computed key and ``required_columns`` were set when (:pr:`79`)
- fixed issue when the ``filters`` containing a computed key matched subsets/messages where the computed key value was missing (:pr:`79`)
