CREATE TABLE users
(
  id SERIAL PRIMARY KEY,
  tg_id INTeger unique,
  url VARCHAR(2048) ,
  login VARCHAR(2048) ,
  "password" VARCHAR(2048) ,
  tgname VARCHAR(2048)

);
CREATE TABLE history(
    ID SERIAL primary key,
    user_id integer,
    foreign key (user_id) REFERENCES users(ID),
    is_old bool default false not null,
    request text,
    response text
);





