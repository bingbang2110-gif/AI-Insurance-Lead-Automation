# AI Insurance Lead Qualification & Sales Automation

An AI-powered insurance lead qualification system built with FastAPI, OpenRouter AI, SQLAlchemy, and SQLite.

## Project Overview

This project automates the early stage of insurance lead qualification.

The system collects customer information through a conversational API, extracts structured insurance data using AI, calculates a lead score, assigns a priority level, stores the lead in a database, and generates a lead summary.

## Architecture

Customer
?
FastAPI Chat API
?
OpenRouter AI
?
Structured Lead Information
?
Lead Scoring
?
Priority Assignment
?
SQLite Database
?
Dashboard

## Current Features

- AI-based extraction of insurance lead information
- Conversational lead information collection
- Structured lead data storage
- Lead scoring from 0 to 100
- Automatic priority assignment
- Automatic lead summary generation
- Lead search and filtering
- Lead statistics
- Lead CRUD operations
- Insurance lead dashboard
- Automation-ready lead completion endpoint
- REST API documentation with FastAPI Swagger

## Technology Stack

- Python
- FastAPI
- OpenRouter API
- SQLAlchemy
- SQLite
- Pydantic
- HTML / JavaScript
- Chart.js

## Lead Qualification

The system evaluates information such as:

- Contact information
- Vehicle information
- Current insurance status
- Coverage type
- Policy expiry
- Urgency

The collected information is converted into a lead score and priority.

## Automation Architecture

The API includes an automation-ready endpoint for completed leads.

Future automation architecture:

Customer
?
FastAPI + AI
?
Lead Qualification
?
Completed Lead
?
Webhook
?
n8n
?
Sales Notification / CRM

## Example Use Case

A customer provides information about their vehicle, current insurance, desired coverage, and urgency.

The AI extracts the structured information and the system produces:

- Lead score
- Lead priority
- Lead summary
- Structured database record

## Project Status

Current stage:

AI lead qualification and FastAPI backend completed.

Next stage:

n8n workflow integration and sales automation.

## Security

API keys and environment variables are stored locally and are not included in the public portfolio repository.

## Author

AI Automation Portfolio Project
