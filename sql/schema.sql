drop table if exists entries;
drop table if exists art;
create table entries (
id integer primary key autoincrement,
nath text,
mplace text,
mmonth text, 
mday text,
mtime text,
telephone text
);

create table art (
id integer primary key autoincrement,
poetryname text,
poetry text
);

