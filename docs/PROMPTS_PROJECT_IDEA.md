# PROMPTS_PROJECT_IDEA.md

## Prompt 1

### User Prompt Summary
- Team-use AI-assisted full stack project
- Social workout club portal
- Member registration/sign in
- Guest access
- Time-slot system from 9am–9pm
- Max 20 users per slot
- Upper body / lower body workout categories
- AI selects 10-minute workout video for public broadcast
- Exploring CrewAI roles
- Development using VS Code, Codex, GitHub repo, VM setup
- Asked for APIs, frameworks, languages, database, backend recommendations

---

### Suggestions / Decisions

#### Project Idea
- Project Name: FitHub AI
- AI-assisted social workout club portal
- Multi-user dashboard with shared workout sessions

#### Core Features
- Member registration/login
- Guest access
- Dashboard
- Time-slot booking
- Capacity limit enforcement
- Public workout broadcast page
- AI-selected workout videos

#### CrewAI Roles
Accepted:
- Trainer Agent
- Safety Checker Agent
- Schedule Agent
- Admin Assistant Agent

Rejected:
- Summary Agent

#### AI Feedback Logic
- Like/dislike feedback retained
- Trainer Agent reviews feedback
- Future video selection influenced by feedback
- Poorly rated videos deprioritized
- Frequently liked channels/categories prioritized

#### APIs Required
- OpenAI API
- YouTube Data API v3

#### APIs Not Required
- Payment APIs
- Wearable APIs
- Google login APIs
- Calendar APIs

#### Recommended Tech Stack
Frontend:
- React
- Vite

Backend:
- Python
- FastAPI

AI:
- CrewAI

Database:
- SQLite

ORM:
- SQLAlchemy

Development Environment:
- VS Code
- Codex
- Git
- GitHub

#### Applications To Install
- Python 3.10+
- Node.js
- npm
- VS Code
- Git
- SQLite Browser (optional)
- Browser
- FastAPI
- CrewAI
- React/Vite tooling

#### Database Tables
- users
- time_slots
- slot_signups
- workout_categories
- video_sessions
- feedback

#### ORM Clarification
- ORM = Object Relational Mapper
- SQLAlchemy recommended
- Allows database interaction through Python objects/classes instead of raw SQL
