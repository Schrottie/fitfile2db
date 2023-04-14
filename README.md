# FitFile2SQLite

```markdown
Author:         Maik 'Schrottie' Bischoff
Decription:     Parse Garmin .fit files and write the data to a CSV file or database.
Version:        0.3
Date:           13.04.2023
Requires:       [dtcooper/python-fitparse](https://github.com/dtcooper/python-fitparse)
```
## How to use:

Just download script and (default) database, set up variables and run. :-)

## Background:

The script was primarily created in order to be able to evaluate the radar data of a Garmin Varia radar. In order to have the data in the .fit file, the [MyBikeRadarTraffic](https://apps.garmin.com/en-US/apps/c5d949c3-9acb-4e00-bb2d-c3b871e9e733) data field must be installed and used at least once (it does not matter whether it is used on a visible or hidden page).
However, it can of course also be used to aggregate the data for other purposes and then use it via CSV export or directly from the SQLite database.

## Whats next? Wishes?

<ul>
    <li>specifying the data types of known fields</li>
    <li>logging of all steps in the database</li>
    <li>separation of path and file name of the known files</li>
    <li>different tables for different .fit data sources (e.g. Fenix watch for running, Edge with radar for cycling, etc.) - or alternatively: an additional field in the database table in which the type of sport and/or origin of the .fit file is specified</li>
</ul>

## Change-/Versionlog:

<table>
    <tr>
        <td>
            <span style="font-size: 85%;font-family: monospace">0.3:</span>
        </td>
        <td>
            <ul style="font-size: 85%;font-family: monospace">
                <li>Added function to convert mph to kph</li>
                <li>Added a function for write data into database.
                    <ul>
                        <li>convert some fields to correct datatype</li>
                        <li>check whether all fields from the current .fit-file exist in an existing table, if necessary updating the table with the new fields</li>
                    </ul>
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td>
            <span style="font-size: 85%;font-family: monospace">0.2:</span>
        </td>
        <td>
            <ul style="font-size: 85%;font-family: monospace">
                <li>Added a function to recursively search a directory for .fit files to allow processing multiple files at the same time.</li>
                <li>Adjusting the field label for the longitude (position_long --> position_lon) so that the field is recognized properly when the data is processed further (e.g. in ArcGIS Pro)</li>
            </ul>
        </td>
    </tr>
    <tr>
        <td>
            <span style="font-size: 85%;font-family: monospace">0.1:</span>
        </td>
        <td>
            <ul style="font-size: 85%;font-family: monospace">
                <li>Basic function for processing a .fit file.</li>
                <li>Converting the crude Garmin coordinate format (semicircles) into 'real' coordinates.</li>
            </ul>
        </td>
    </tr>
</table>
