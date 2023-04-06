# FitFile2DB

```markdown
Autor:          Maik 'Schrottie' Bischoff
Beschreibung:   Parse Garmin .fit files and write the data to a CSV file or database.
Version:        0.2
Stand:          06.04.2023
```
##### ToDo:

<ul style="font-size: 85%;font-family: monospace">
    <li>Function to create a table in the database with the fields from the .fit-file.</li>
    <li>Function for checking whether all fields from the current .fit-file exist in an existing table, if necessary updating the table with the new fields.</li>
</ul>

##### Change-/Versionlog:

<table>
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
