-- Database initialization script for Student Management Application
-- Automatically executed on first boot by MySQL container entrypoint

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL
);

INSERT INTO students (name, department) VALUES
('Rahul', 'CSE'),
('Priya', 'ISE'),
('Arjun', 'ECE');
