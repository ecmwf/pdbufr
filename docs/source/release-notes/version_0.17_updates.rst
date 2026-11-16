Version 0.17 Updates
/////////////////////////


Version 0.17.0
===============

New features
---------------------

Improvements to the :ref:`synop reader <synop-reader>`:

- Values encoded in the BUFR message with two periods (a start and an end), e.g. -24 h and 0 h, were previously wrongly reported back with the period "0h". This has been fixed: the period is now determined correctly from both values. See :ref:`synop-period-lag`.
- All the resulting periods are now non-negative. Periods encoded in the BUFR message with a positive value, e.g. 24 h instead of -24 h, are automatically converted and appear as "24h" in the result. See :ref:`synop-periods`.
- Periods that end before the observation time (encoded in the BUFR message as a start/end pair) are now read correctly and named ``<duration>_lag<offset>``, e.g. "max_t2m_24h_lag6h". Previously only the second (end) period of the pair was used, which gave a wrong result, e.g. a period of 24 hours ending 6 hours before the observation time was reported as "6h". See :ref:`synop-period-lag`.
- When several sensors report the same parameter and period, the value from the sensor closest to the nominal height is used (2 m for the maximum/minimum 2 m temperature, 10 m for the maximum wind gust). Sensors below 0.5 m are ignored for the temperature parameters; a value reported without a height is accepted but ranks after one with a height. See :ref:`synop-levels`.

See the notebook example:

    - :ref:`/tutorials/synop/r_synop_periods_levels.ipynb`


Changes in behaviour
---------------------

The column names of the default :ref:`synop reader <synop-reader>` output have changed (see :ref:`synop-periods`):

- There are no more "_nan" columns: a value reported without a period is written to the plain column named after the parameter, e.g. "precipitation".

See the notebook example:

    - :ref:`/tutorials/synop/r_synop_overview.ipynb`
