-- College Event Management System (CEMS) Database Creation Script
-- Created: May 7, 2025

-- Drop database if it exists and create a new one
DROP DATABASE IF EXISTS cems_db;
CREATE DATABASE cems_db;
USE cems_db;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS=1;

-- Create tables based on the SQLAlchemy models

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    organization VARCHAR(255),
    contact_number VARCHAR(20),
    description TEXT,
    college_name VARCHAR(200),
    department VARCHAR(100),
    year_of_study VARCHAR(20)
);

-- Events table
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    title VARCHAR(200),
    date VARCHAR(10) NOT NULL,
    start_date DATETIME,
    end_date DATETIME,
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    description TEXT,
    tag VARCHAR(50),
    category VARCHAR(50),
    venue VARCHAR(255),
    image VARCHAR(255),
    cover_image VARCHAR(255),
    video VARCHAR(255),
    brochure VARCHAR(255),
    tags VARCHAR(255),
    schedule TEXT,
    price FLOAT DEFAULT 0,
    is_free BOOLEAN DEFAULT TRUE,
    seats_total INT DEFAULT 0,
    seats_available INT DEFAULT 0,
    registration_end_date DATETIME,
    is_featured BOOLEAN DEFAULT FALSE,
    parent_event_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    organiser_id INT,
    custom_data TEXT,
    ui_theme VARCHAR(50) DEFAULT 'minimalistic',
    FOREIGN KEY (parent_event_id) REFERENCES events(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (organiser_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Registrations table
CREATE TABLE registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_id VARCHAR(100),
    payment_status VARCHAR(20) DEFAULT 'pending',
    college_name VARCHAR(200),
    department VARCHAR(100),
    year_of_study VARCHAR(20),
    registration_data TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Resources table
CREATE TABLE resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    total_quantity INT DEFAULT 0,
    available_quantity INT DEFAULT 0,
    image VARCHAR(255),
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Resource Allocations table
CREATE TABLE resource_allocations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL,
    event_id INT NOT NULL,
    quantity INT DEFAULT 0,
    allocated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    returned_at DATETIME,
    status VARCHAR(20) DEFAULT 'allocated',
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    user_id INT,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Event Tags table
CREATE TABLE event_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create a reference table for study years
CREATE TABLE study_years (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year_name VARCHAR(20) NOT NULL UNIQUE,
    display_name VARCHAR(50) NOT NULL,
    sort_order INT NOT NULL
);

-- Insert standard academic years
INSERT INTO study_years (year_name, display_name, sort_order) VALUES
('1st_year', '1st Year', 1),
('2nd_year', '2nd Year', 2),
('3rd_year', '3rd Year', 3),
('4th_year', '4th Year', 4),
('5th_year', '5th Year', 5),
('pg', 'Post Graduate', 6),
('phd', 'PhD', 7);

-- Insert sample user accounts for testing
INSERT INTO users (name, email, password, role, college_name, department, year_of_study) VALUES 
('System Admin', 'admin@example.com', '$2b$12$XIZ4xRXKScyVpDJwhKyeO.Nkh3V/6LD3fzrzUlCbITz9TlJeg4UdG', 'admin', NULL, NULL, NULL),
('Organiser User', 'organiser@example.com', '$2b$12$XIZ4xRXKScyVpDJwhKyeO.xD7AHk9VPCJBJMQjbxsJ0dlx9rT2rqa', 'organiser', 'ABC College', 'Event Management', NULL),
('Student 1', 'student1@example.com', '$2b$12$XIZ4xRXKScyVpDJwhKyeO.d4JHaYiX1MIPo1Qm5nFd9uo4QJi1Eju', 'participant', 'XYZ Engineering College', 'Computer Science', '2nd_year'),
('Student 2', 'student2@example.com', '$2b$12$XIZ4xRXKScyVpDJwhKyeO.d4JHaYiX1MIPo1Qm5nFd9uo4QJi1Eju', 'participant', 'ABC Arts College', 'Fine Arts', '3rd_year'),
('Faculty Member', 'faculty@example.com', '$2b$12$XIZ4xRXKScyVpDJwhKyeO.fIPkqDk9lEwW0HTRvHXfZwqY4yQ7AOG', 'participant', 'XYZ Engineering College', 'Computer Science', NULL);

-- Insert sample event tags
INSERT INTO event_tags (name) VALUES
('Tech'), ('Art'), ('Workshop'), ('Seminar'), ('Competition'), 
('Conference'), ('Cultural'), ('Sports'), ('Academic'), ('Hackathon');

-- Insert sample resources
INSERT INTO resources (name, category, description, total_quantity, available_quantity) VALUES
('Projector', 'Equipment', 'High-definition projector for presentations', 10, 10),
('Speaker System', 'Audio', 'Professional audio system with 2 speakers and mixer', 5, 5),
('Chairs', 'Furniture', 'Stackable chairs for audience seating', 200, 200),
('Tables', 'Furniture', 'Foldable tables for exhibitions', 50, 50),
('Microphones', 'Audio', 'Wireless handheld microphones', 15, 15),
('Laptops', 'Equipment', 'Dell laptops for workshop participants', 25, 25),
('Stage Lights', 'Lighting', 'Programmable RGB stage lighting', 20, 20);

-- Insert sample events
INSERT INTO events (name, title, date, start_date, end_date, start_time, end_time, description, 
                   category, venue, is_free, seats_total, seats_available, created_by, organiser_id) VALUES
('Annual Tech Symposium', 'Tech Symposium 2025', '2025-06-15', '2025-06-15 09:00:00', '2025-06-16 17:00:00', 
 '09:00', '17:00', 'Join us for the annual tech symposium featuring keynote speakers from leading tech companies.',
 'Tech', 'Main Auditorium', FALSE, 200, 200, 1, 2),
 
('Art Exhibition', 'Student Art Showcase', '2025-05-20', '2025-05-20 10:00:00', '2025-05-22 18:00:00', 
 '10:00', '18:00', 'A showcase of stunning artwork created by our talented students.',
 'Art', 'Art Gallery', TRUE, 100, 100, 1, 2),
 
('Career Workshop', 'Building Your Professional Brand', '2025-05-25', '2025-05-25 14:00:00', '2025-05-25 16:00:00', 
 '14:00', '16:00', 'Learn how to build your professional brand and improve your job prospects.',
 'Workshop', 'Seminar Hall B', TRUE, 50, 50, 2, 2);

-- Add sample registrations with college information
INSERT INTO registrations (event_id, user_id, payment_status, college_name, department, year_of_study) VALUES
(1, 3, 'completed', 'XYZ Engineering College', 'Computer Science', '2nd_year'),
(1, 4, 'completed', 'ABC Arts College', 'Fine Arts', '3rd_year'),
(2, 3, 'completed', 'XYZ Engineering College', 'Computer Science', '2nd_year');

-- Add a sample resource allocation
INSERT INTO resource_allocations (resource_id, event_id, quantity, status) VALUES
(1, 1, 2, 'allocated'),  -- 2 projectors for Tech Symposium
(2, 1, 1, 'allocated'),  -- 1 speaker system for Tech Symposium
(3, 1, 100, 'allocated'), -- 100 chairs for Tech Symposium
(7, 2, 10, 'allocated');  -- 10 stage lights for Art Exhibition

-- Create a departments reference table for common departments
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL
);

-- Insert common departments
INSERT INTO departments (name, category) VALUES
('Computer Science', 'Engineering'),
('Information Technology', 'Engineering'),
('Electrical Engineering', 'Engineering'),
('Mechanical Engineering', 'Engineering'),
('Civil Engineering', 'Engineering'),
('Electronics & Communication', 'Engineering'),
('Chemistry', 'Science'),
('Physics', 'Science'),
('Mathematics', 'Science'),
('Biology', 'Science'),
('Economics', 'Arts'),
('History', 'Arts'),
('English Literature', 'Arts'),
('Fine Arts', 'Arts'),
('Business Administration', 'Business'),
('Commerce', 'Business'),
('Psychology', 'Science'),
('Sociology', 'Arts');