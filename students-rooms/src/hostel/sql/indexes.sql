CREATE INDEX IF NOT EXISTS idx_students_room_birthday
    ON students (room, birthday);

CREATE INDEX IF NOT EXISTS idx_students_room_sex
    ON students (room, sex);

ANALYZE students;
