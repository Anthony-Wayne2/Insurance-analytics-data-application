CREATE DATABASE IF NOT EXISTS insurance_analytics;
USE insurance_analytics;

CREATE TABLE IF NOT EXISTS patients (
    patient_id      VARCHAR(20) PRIMARY KEY,
    first_name      VARCHAR(50),
    last_name       VARCHAR(50),
    age				int4(2),
    gender          VARCHAR(10),
    address			varchar(20),
    city            VARCHAR(50),
    state           VARCHAR(20),
    zip_code        varchar(45),
    phone           int4(25)
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id     VARCHAR(20) PRIMARY KEY,
	name			VARCHAR(100),
    specialty       VARCHAR(60),
    city            VARCHAR(50),
    state           VARCHAR(20),
    zip_code        varchar(45),
    phone			int4(25)
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id        VARCHAR(20) PRIMARY KEY,
    patient_id      VARCHAR(20),
    provider_id     VARCHAR(20),
    claim_date      DATE,
	claim_amount    DECIMAL(12,2),
    status          VARCHAR(20),
    FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id      VARCHAR(20) PRIMARY KEY,
    claim_id        VARCHAR(20),
    provider_id		varchar(20),
    claim_date		date,
    claim_amount	decimal(18,6),
    status			varchar(20),
    payment_id		varchar(20),
    payment_date    DATE,
    payment_amount     DECIMAL(18,6),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);