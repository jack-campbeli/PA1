CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Comment CASCADE;
DROP TABLE IF EXISTS Tag CASCADE;
DROP TABLE IF EXISTS Photo CASCADE;
DROP TABLE IF EXISTS Album CASCADE;
DROP TABLE IF EXISTS Friend CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
	user_id int AUTO_INCREMENT,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	email VARCHAR(255) UNIQUE NOT NULL,
	password VARCHAR(255) NOT NULL,
	dob DATE NOT NULL,
	hometown VARCHAR(100),
	gender VARCHAR(50),
	contribution_score int4 DEFAULT 0,

	CONSTRAINT user_pk PRIMARY KEY (user_id),
	CHECK (gender = 'female' OR gender = 'male' OR gender = 'n/a'),
	CHECK (contribution_score >= 0)
);

CREATE TABLE Photo (
--     album_id int4 NOT NULL,
    
	photo_id int4 AUTO_INCREMENT,
	user_id int4,
	imgdata longblob,
	caption VARCHAR(255),
	INDEX upid_idx (user_id),
	CONSTRAINT photo_pk PRIMARY KEY (photo_id)

-- 	FOREIGN KEY (user_id) 
-- 		REFERENCES Users (user_id) 
-- 		ON DELETE CASCADE,
-- 	FOREIGN KEY (album_id) 	
-- 		REFERENCES Album (album_id)
);

CREATE TABLE Friend (
  user_id INT NOT NULL,
  friend_id INT NOT NULL,

  PRIMARY KEY (user_id, friend_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (friend_id) REFERENCES Users(user_id),
  CHECK (user_id <> friend_id)
);

CREATE TABLE Album (
	album_id INT AUTO_INCREMENT,
	user_id INT NOT NULL,
	a_name VARCHAR(255) NOT NULL,
	creation_date VARCHAR(255) NOT NULL,
    
	CONSTRAINT album_pk PRIMARY KEY (album_id),
	FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

CREATE TABLE Tag (
	tag_name VARCHAR(255) UNIQUE,
	photo_id INT,
    
	CONSTRAINT tag_pk PRIMARY KEY (tag_name, photo_id),
	FOREIGN KEY (photo_id) REFERENCES Photo (photo_id) ON DELETE CASCADE
);

CREATE TABLE Comment (
	comment_id INT4 AUTO_INCREMENT,
	user_id INT4 NOT NULL,
	photo_id INT4 NOT NULL,
	date DATE NOT NULL,
	text longtext NOT NULL,
    
	CONSTRAINT comment_pk PRIMARY KEY (comment_id),
	FOREIGN KEY (photo_id) REFERENCES Photo (photo_id),
	FOREIGN KEY (user_id) REFERENCES Users (user_id)
);