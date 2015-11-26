create table images (
    id serial primary key,
    image varchar(128),
    file varchar(255),
    created_at timestamp without time zone default timezone('utc'::text, now())
);
