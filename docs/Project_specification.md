# Project_specification.md

# FitHub AI
AI-Assisted Social Workout Club Portal

---

# 1. Project Overview

FitHub AI is a prototype social workout portal designed for team and organizational use.

Members can:
- Register and sign in
- Select workout time slots
- Join shared workout sessions
- Watch AI-selected workout videos

The system supports:
- Shared resources
- Multiple concurrent users
- AI-assisted decision making
- Public workout broadcasting

This project is intended to satisfy the AI-assisted team-use full stack project requirement.

---

# 2. Core Functional Requirements

## User Types

### Member
- Register account
- Login
- Select preferred workout slot
- Watch workout broadcast
- Submit video feedback

### Guest (Not implemented)
- Limited dashboard access
- Can view public broadcast
- Cannot reserve slots

### Admin
- Monitor active slots
- View/Edit member occupancy
- Override workout video if required

---

# 3. Member Information

Collected during registration:
- Name
- Age
- Preferred time slots

---

# 4. Time Slot Rules

- Slots operate hourly
- Operating hours: 9am–9pm (Date selection not included)
- Maximum 20 signed-in members per slot
- Capacity restriction helps reduce network load

---

# 5. Workout Categories

Prototype categories:
- Upper Body
- Lower Body
- Cardio

---

# 6. AI Workflow

The AI system selects a suitable workout video for the active time slot.

Requirements:
- Video duration approximately 10 minutes
- Video category must match selected workout category
- Video must be appropriate and safe for general users
- Video must be embeddable and playable

---

# 7. CrewAI Agents (Later switched to deterministic code-based agents)

## Trainer Agent
Responsibilities:
- Search/select workout videos
- Review user feedback
- Improve future selections

## Safety Checker Agent
Responsibilities:
- Reject unsafe or unrelated videos
- Avoid extreme/intense unsuitable content

## Schedule Agent
Responsibilities:
- Monitor slot occupancy
- Enforce maximum user limits
- Coordinate session timing

## Admin Assistant Agent
Responsibilities:
- Provide admin summaries
- Assist admin operations
- Monitor system usage

---

# 8. Feedback System

Members can:
- Like videos
- Dislike videos

Purpose:
- Improve future AI video recommendations
- Avoid unpopular videos
- Prefer highly rated channels/categories

The Trainer Agent reviews feedback before future video selection.

---

# 9. Recommended Technology Stack

## Frontend
- React
- Vite

Purpose:
- Fast prototype development
- Responsive dashboard UI

## Backend
- Python
- FastAPI

Purpose:
- API development
- AI orchestration
- Authentication
- Session management

## AI Layer
- CrewAI

Purpose:
- Multi-agent coordination
- Video recommendation workflow

## Database
- SQLite

Purpose:
- Lightweight local database
- Simple prototype deployment

## ORM
- SQLAlchemy

Purpose:
- Database interaction using Python objects/classes
- Reduces raw SQL usage

---

# 10. APIs Required

## OpenAI API (not used by application)
Purpose:
- AI reasoning
- Agent decision-making
- (OpenAI/Ollama-style reasoning is no longer central to the implemented workflow.)

## YouTube Data API v3
Purpose:
- Workout video search
- Video metadata retrieval

---

# 11. APIs Not Required

Not required for prototype:
- Payment APIs
- Wearable APIs
- Google login APIs
- Calendar APIs

---

# 12. Suggested Database Tables

## users
Stores:
- Member/admin accounts

## time_slots
Stores:
- Available workout slots

## slot_signups
Stores:
- User reservations

## workout_categories
Stores:
- Upper body / lower body categories

## video_sessions
Stores:
- Selected workout videos

## feedback
Stores:
- Like/dislike responses

---

# 13. Suggested Project Structure

project/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt / package.json
├── src/
├── tests/
├── docs/
├── scripts/
├── assets/
└── data/

---

# 14. Development Environment

Recommended setup:
- Virtual machine environment
- Visual Studio Code
- Codex integration
- GitHub local repository access

---

# 15. Applications To Install

Required:
- Python 3.10+
- Node.js
- npm
- Git
- VS Code
- Browser

Recommended:
- SQLite Browser
- CrewAI
- FastAPI
- React/Vite tooling

---

# 16. Prototype Scope

This project should remain:
- Small
- Demonstrable
- AI-assisted
- Easy to explain during presentation

Avoid:
- Complex enterprise architecture
- Excessive features
- Mobile applications
- Real-time streaming infrastructure

---

# 17. Alignment With Programme Goals

This project demonstrates:
- Full stack development
- AI-assisted workflows
- Multi-user system design
- Prompt engineering
- AI agent orchestration (not implemented)
- Team-use application architecture
