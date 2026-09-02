CREATE TYPE student_sex AS ENUM ('M', 'F');

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER NOT NULL CHECK (id >= 0),
    name VARCHAR(64) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER NOT NULL CHECK (id >= 0),
    name VARCHAR(128) NOT NULL,
    birthday DATE NOT NULL,
    sex student_sex NOT NULL,
    room INTEGER NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_students_room
        FOREIGN KEY (room) REFERENCES rooms (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
