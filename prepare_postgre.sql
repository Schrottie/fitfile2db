CREATE TABLE fitfile_userdata (
    id SERIAL PRIMARY KEY,
);

CREATE TABLE fitfile_data (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(MAX) NOT NULL
);

CREATE TABLE fitfile_totals (
    id SERIAL PRIMARY KEY,
);

CREATE TABLE known_fitfiles (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(MAX) NOT NULL
);
