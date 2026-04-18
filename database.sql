SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS foodbank;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS private_booking;
DROP TABLE IF EXISTS private_slot;
DROP TABLE IF EXISTS trainer_booking;
DROP TABLE IF EXISTS trainer_slot;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS trainer;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS plans;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(100) NOT NULL,
    role ENUM('admin', 'member', 'trainer') NOT NULL
);

CREATE TABLE plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL,
    plan_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE admin (
    username VARCHAR(50) PRIMARY KEY,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE member (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    dob DATE,
    join_date DATE,
    email VARCHAR(120),
    fine DECIMAL(10,2) NOT NULL DEFAULT 0,
    plan_id INT,
    daily_calorie_limit INT NOT NULL DEFAULT 2000,
    expected_workout_minutes INT NOT NULL DEFAULT 60,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
);

CREATE TABLE trainer (
    trainer_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    dob DATE,
    specialization VARCHAR(100),
    experience INT NOT NULL DEFAULT 0,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE trainer_slot (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    trainer_id INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id) ON DELETE CASCADE
);

CREATE TABLE trainer_booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    trainer_id INT NOT NULL,
    slot_id INT NOT NULL,
    booking_date DATE NOT NULL,
    status ENUM('booked', 'completed', 'missed') NOT NULL DEFAULT 'booked',
    fine_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (member_id) REFERENCES member(member_id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES trainer_slot(slot_id) ON DELETE CASCADE,
    UNIQUE KEY unique_trainer_slot_day (trainer_id, slot_id, booking_date)
);

CREATE TABLE private_slot (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL
);

CREATE TABLE private_booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_id INT NOT NULL,
    member_id INT NOT NULL,
    booking_date DATE NOT NULL,
    FOREIGN KEY (slot_id) REFERENCES private_slot(slot_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES member(member_id) ON DELETE CASCADE,
    UNIQUE KEY unique_private_slot_day (slot_id, booking_date)
);

CREATE TABLE attendance (
    member_id INT NOT NULL,
    date DATE NOT NULL,
    entry TIME NOT NULL,
    exit_time TIME,
    PRIMARY KEY (member_id, date),
    FOREIGN KEY (member_id) REFERENCES member(member_id) ON DELETE CASCADE
);

CREATE TABLE foodbank (
    food VARCHAR(100) PRIMARY KEY,
    calorie INT NOT NULL
);

CREATE TABLE logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    food VARCHAR(100) NOT NULL,
    member_id INT NOT NULL,
    calorie DECIMAL(10,2) NOT NULL,
    log_date DATE NOT NULL,
    portion DECIMAL(5,2) NOT NULL DEFAULT 1,
    FOREIGN KEY (food) REFERENCES foodbank(food),
    FOREIGN KEY (member_id) REFERENCES member(member_id) ON DELETE CASCADE
);

INSERT INTO users (username, password, role) VALUES
('admin1', 'admin123', 'admin'),
('member1', 'pass123', 'member'),
('member2', 'pass123', 'member'),
('member3', 'pass123', 'member'),
('member4', 'pass123', 'member'),
('member5', 'pass123', 'member'),
('member6', 'pass123', 'member'),
('member7', 'pass123', 'member'),
('member8', 'pass123', 'member'),
('member9', 'pass123', 'member'),
('member10', 'pass123', 'member'),
('trainer1', 'pass123', 'trainer'),
('trainer2', 'pass123', 'trainer'),
('trainer3', 'pass123', 'trainer'),
('trainer4', 'pass123', 'trainer'),
('trainer5', 'pass123', 'trainer');

INSERT INTO admin (username) VALUES ('admin1');

INSERT INTO plans (plan_name, plan_price) VALUES
('Basic Monthly', 35.00),
('Standard Monthly', 55.00),
('Premium Monthly', 80.00),
('Student Plan', 30.00),
('Family Plan', 120.00);

INSERT INTO member
(username, name, gender, dob, join_date, email, fine, plan_id, daily_calorie_limit, expected_workout_minutes) VALUES
('member1', 'Ariana Khan', 'Female', '2000-01-12', '2026-01-05', 'ariana@example.com', 0, 1, 2000, 60),
('member2', 'Rafi Ahmed', 'Male', '1998-07-22', '2026-01-08', 'rafi@example.com', 0, 2, 2400, 60),
('member3', 'Nila Das', 'Female', '2002-04-18', '2026-01-10', 'nila@example.com', 0, 2, 1900, 45),
('member4', 'Sami Rahman', 'Male', '1995-09-03', '2026-01-13', 'sami@example.com', 0, 3, 2600, 75),
('member5', 'Maya Chowdhury', 'Female', '1999-11-30', '2026-01-15', 'maya@example.com', 0, 1, 2000, 60),
('member6', 'Tanvir Islam', 'Male', '1997-03-19', '2026-01-18', 'tanvir@example.com', 0, 4, 2300, 60),
('member7', 'Lamia Sultana', 'Female', '2001-06-14', '2026-01-21', 'lamia@example.com', 0, 2, 1900, 45),
('member8', 'Jamal Hossain', 'Male', '1994-12-01', '2026-01-23', 'jamal@example.com', 0, 3, 2500, 75),
('member9', 'Farah Noor', 'Female', '2003-02-09', '2026-01-25', 'farah@example.com', 0, 4, 1800, 45),
('member10', 'Omar Malik', 'Male', '1996-08-27', '2026-01-29', 'omar@example.com', 0, 5, 2400, 60);

INSERT INTO trainer
(username, name, gender, dob, specialization, experience) VALUES
('trainer1', 'Hasan Ali', 'Male', '1988-05-11', 'Strength', 8),
('trainer2', 'Sara Akter', 'Female', '1991-10-02', 'Yoga', 6),
('trainer3', 'Imran Karim', 'Male', '1985-01-20', 'Cardio', 10),
('trainer4', 'Priya Sen', 'Female', '1993-07-16', 'Pilates', 5),
('trainer5', 'Mahin Chowdhury', 'Male', '1990-03-06', 'Weight Loss', 7);

INSERT INTO trainer_slot (trainer_id, start_time, end_time) VALUES
(1, '08:00:00', '09:00:00'),
(1, '10:00:00', '11:00:00'),
(1, '17:00:00', '18:00:00'),
(2, '07:00:00', '08:00:00'),
(2, '15:00:00', '16:00:00'),
(3, '09:00:00', '10:00:00'),
(3, '18:00:00', '19:00:00'),
(4, '11:00:00', '12:00:00'),
(4, '16:00:00', '17:00:00'),
(5, '12:00:00', '13:00:00'),
(5, '19:00:00', '20:00:00');

INSERT INTO trainer_booking (member_id, trainer_id, slot_id, booking_date, status, fine_amount) VALUES
(1, 1, 1, CURDATE(), 'booked', 0),
(2, 2, 4, CURDATE(), 'completed', 0),
(3, 3, 6, CURDATE(), 'missed', 100),
(4, 4, 8, DATE_ADD(CURDATE(), INTERVAL 1 DAY), 'booked', 0),
(5, 5, 10, DATE_ADD(CURDATE(), INTERVAL 1 DAY), 'booked', 0),
(6, 1, 2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'completed', 0),
(7, 2, 5, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'missed', 100),
(8, 3, 7, DATE_ADD(CURDATE(), INTERVAL 2 DAY), 'booked', 0),
(9, 4, 9, DATE_ADD(CURDATE(), INTERVAL 2 DAY), 'booked', 0),
(10, 5, 11, DATE_ADD(CURDATE(), INTERVAL 3 DAY), 'booked', 0);

UPDATE member
SET fine = (
    SELECT COALESCE(SUM(fine_amount), 0)
    FROM trainer_booking
    WHERE trainer_booking.member_id = member.member_id
      AND trainer_booking.status = 'missed'
);

INSERT INTO private_slot (start_time, end_time) VALUES
('06:00:00', '07:00:00'),
('07:00:00', '08:00:00'),
('08:00:00', '09:00:00'),
('09:00:00', '10:00:00'),
('10:00:00', '11:00:00'),
('11:00:00', '12:00:00'),
('15:00:00', '16:00:00'),
('16:00:00', '17:00:00'),
('17:00:00', '18:00:00'),
('18:00:00', '19:00:00');

INSERT INTO private_booking (slot_id, member_id, booking_date) VALUES
(1, 1, CURDATE()),
(2, 2, CURDATE()),
(3, 3, DATE_ADD(CURDATE(), INTERVAL 1 DAY)),
(4, 4, DATE_ADD(CURDATE(), INTERVAL 1 DAY)),
(5, 5, DATE_ADD(CURDATE(), INTERVAL 2 DAY));

INSERT INTO attendance (member_id, date, entry, exit_time) VALUES
(1, CURDATE(), '08:00:00', '09:20:00'),
(2, CURDATE(), '07:15:00', '08:00:00'),
(3, CURDATE(), '09:10:00', '09:45:00'),
(4, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '18:00:00', '19:30:00'),
(5, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '10:00:00', '10:50:00'),
(6, DATE_SUB(CURDATE(), INTERVAL 2 DAY), '12:00:00', '13:10:00'),
(7, DATE_SUB(CURDATE(), INTERVAL 2 DAY), '15:00:00', '15:35:00'),
(8, DATE_SUB(CURDATE(), INTERVAL 3 DAY), '16:00:00', '17:40:00'),
(9, DATE_SUB(CURDATE(), INTERVAL 3 DAY), '11:00:00', '11:30:00'),
(10, DATE_SUB(CURDATE(), INTERVAL 4 DAY), '19:00:00', '20:05:00');

INSERT INTO foodbank (food, calorie) VALUES
('Rice Bowl', 300),
('Chicken Breast', 220),
('Egg', 78),
('Banana', 105),
('Apple', 95),
('Protein Shake', 180),
('Salad', 120),
('Oatmeal', 150),
('Fish Curry', 260),
('Yogurt', 140),
('Peanut Butter Toast', 280),
('Vegetable Soup', 110);

INSERT INTO logs (food, member_id, calorie, log_date, portion) VALUES
('Rice Bowl', 1, 300, CURDATE(), 1),
('Chicken Breast', 1, 220, CURDATE(), 1),
('Banana', 1, 105, CURDATE(), 1),
('Oatmeal', 2, 150, CURDATE(), 1),
('Protein Shake', 2, 180, CURDATE(), 1),
('Salad', 3, 120, CURDATE(), 1),
('Fish Curry', 4, 260, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 1),
('Apple', 5, 95, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 1),
('Yogurt', 6, 140, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 1),
('Egg', 7, 156, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 2);
