# PROMPTS_IMPLEMENTATION.md

This document records prompts, AI suggestions, decisions, and implementation summaries for Project 2. It is maintained so evaluators can review how AI was used as a co-developer.

Note: early prompts record an initial CrewAI-oriented design exploration. That direction was superseded in Prompt 24; the current implementation uses deterministic backend services with an optional LiteLLM review hook, not CrewAI.

## Prompt 1

### User Prompt

> I am developing a full stack browser dashboard application as project 2. Refer to the HTML for the Project Delieverables / suggested folder structure. Build file structure scaffold based on suggestion, in accordance with the project_specification.txt. You will then provide a project implementation plan, break down into phases, place the .md document in project 2/ docs folder. You will document every prompt and  a summary of your suggestion, solution given or implementation in projects 2/docs/PROMPTS_IMPLEMENTATION.md. README.md will be written for an audience that is evaluating me as a AI-project developer (for context read HTML), the README.md requirements are specified in HTML. Any questions regarding this prompt be brief.

### Context Reviewed

- `Project_specification.md`
- `PROMPTS_PROJECT_DEVELOPMENT.md`
- `Documents/B1 Builders Programme.html`

### Summary of Requirements Identified

- Project 2 is a team, department, or organisational use project.
- Both frontend and backend components are required.
- The repository should follow the suggested structure:
  - `README.md`
  - `LICENSE`
  - `.gitignore`
  - dependency files
  - `src/`
  - `tests/`
  - `docs/`
  - `scripts/`
  - `assets/`
  - `data/`
- README should include:
  - Project title
  - Overview
  - Problem
  - Outcome
  - Demo
  - Technology stack
  - Development approach with AI
  - Installation
  - Usage
  - Project structure
  - Reflection
- FitHub AI specification requires:
  - Member registration and login
  - Guest limited dashboard access
  - Admin monitoring and override
  - Hourly slots from 9am-9pm
  - Maximum 20 signed-in members per slot
  - Upper Body and Lower Body workout categories
  - AI-selected safe approximately 10-minute workout videos
  - CrewAI agents: Trainer, Safety Checker, Schedule, Admin Assistant
  - Feedback via like/dislike
  - React/Vite frontend
  - Python/FastAPI backend
  - SQLite database
  - SQLAlchemy ORM

### AI Suggestion

Create a lightweight but realistic full stack scaffold that keeps the required top-level deliverable structure while separating implementation code into:

- `src/backend/` for FastAPI, database models, services, and AI agents.
- `src/frontend/` for the React/Vite browser dashboard.
- `docs/` for evaluator-facing planning and prompt documentation.

The scaffold should avoid over-engineering at this stage and keep the project demonstrable for an interview.

### Solution Implemented

- Created the requested folder scaffold.
- Added backend starter package with FastAPI app and API status route.
- Added frontend Vite/React starter files with a FitHub AI dashboard placeholder.
- Added `.env.example`, `.gitignore`, `requirements.txt`, and root `package.json`.
- Added `README.md` written for B1 Builders evaluators.
- Added `docs/IMPLEMENTATION_PLAN.md` with phased delivery plan.
- Added this prompt and implementation log.

### Key Decisions

- Used `src/backend/` and `src/frontend/` inside the required `src/` folder to keep the full stack layout clear.
- Kept the top-level structure aligned with the programme document.
- Included both `requirements.txt` and `package.json` because the project uses Python backend and JavaScript frontend tooling.
- Added placeholder code rather than full features in this scaffold phase so future implementation can proceed in focused phases.
- Treated prompt documentation as a living project artifact, not a final-only report.

## Prompt 2

### User Prompt

> what packages need to be installed? what Applications To Install? Inspect,install yourself if you can, if not list what needs to be installed with installation commands. Remember to document the prompts,  refine outputs, and debug issues.

### Inspection Performed

- Inspected local development tools.
- Installed backend dependencies into `.venv`.
- Checked backend scaffold startup and imports.
- Identified missing frontend system tools.

### Results

- Installed Python backend dependencies successfully.
- Confirmed Python, Git, SQLite, and VS Code CLI are available.
- Confirmed Node.js and npm were missing at that point, so frontend packages were pending then.
- Could not install Node.js/npm automatically because system package installation requires unavailable sudo access.
- Later verification confirmed Node.js and npm became available, and frontend dependencies/build were corrected.

### Debug Issue Found

CrewAI needed workspace-local storage configuration in this restricted environment.

### Refinement / Solution

- Added `CREWAI_STORAGE_DIR=.crewai-storage` and `CREWAI_TRACING_ENABLED=false` to `.env.example`.
- Added `.crewai-storage/` and `.local/` to `.gitignore`.
- Verified backend imports using workspace-local CrewAI storage.

### Documentation Added

- Created `docs/INSTALLATION_NOTES.md` with the installation status and remaining setup commands.

## Prompt 3

### User Prompt

> I have obtianed YOUTUBE_API_KEY and OPEN_API_KEY, but my openAI credits are $0, so API request will fail. Another Agent recommended I use Ollama locally, completely free, CrewAI can connect to local Ollama instead of OpenAI API. Is this a correct suggestion? Will my application be able to perform - AI reasoning, Agent decision-making without OpenAI API key? Do I even need OpenAI API key or Ollama in the first place?

### Summary of Guidance

- Confirmed from the installed CrewAI package that CrewAI supports Ollama through its `LLM` configuration and LiteLLM-style provider routing.
- Recommended treating the LLM provider as configurable rather than hard-coding OpenAI.
- Clarified that real CrewAI reasoning needs some LLM provider, but it does not have to be OpenAI.
- Clarified that the prototype can still run core dashboard features with deterministic or mock recommendation logic if no LLM is available.
- Added safe placeholder LLM provider settings to `.env.example` without reading or exposing local secrets from `.env`.

## Prompt 4

### User Prompt

> Alright  I agree with you suggestion. At this juncture I make the decision to use Ollama inplace of OpenAI inorder for CrewAI to perform real reasoning. Update PROMPTS_IMPLEMENATION about the decision made and reason why. Update requirements.txt , Installation_note.md etc about. In .env and config add flag options to swtich between OpenAI and Ollama, but the default being Ollama. So the fallback could be mock/rule-based recommender for this prototype.  Remember to keep .env and .envexample same (except .envexample secrets are empty). What is the next step to take?

### Decision Made

- Ollama is now the default LLM provider for CrewAI reasoning.
- OpenAI remains an optional provider for later use if credits are available.
- The prototype will support mock/rule-based recommendation fallback for demos when no LLM is available.

### Reason

- OpenAI API calls may fail because the available OpenAI credits are currently `$0`.
- Ollama allows local, free LLM execution, which keeps the prototype demonstrable while still supporting real CrewAI agent reasoning.
- A mock fallback protects the demo from local model, API key, or connectivity issues.

### Implementation Summary

- Added provider flags to `.env`, `.env.example`, and backend config.
- Set Ollama as the default provider with `MODEL=ollama/llama3`.
- Added `litellm==1.82.6` to `requirements.txt` because CrewAI uses LiteLLM for provider routing such as Ollama.
- Updated installation notes, README, and implementation plan to reflect Ollama-first AI reasoning with OpenAI optional fallback.

### Debug / Verification

- Initial `litellm>=1.70.0` install selected a newer LiteLLM release that conflicted with CrewAI's OpenAI dependency.
- Pinned `litellm==1.82.6`, which works with `openai>=2.30.0,<3`.
- Verified `pip check` reports no broken requirements.
- Verified `.env` and `.env.example` have the same keys, with `.env.example` keeping secret values empty.
- Verified backend config reads Ollama as the default provider.

## Prompt 5

### User Prompt

> I have installed ollama , with WARNING: No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode. How will this issue affect performance of this application. hwo to resolve this?  ollama pull ...,  done with success. ollama serve - ollama serve returned - Error: listen tcp 127.0.0.1:11434: bind: address already in use

### Guidance / Debug Summary

- Confirmed Ollama is already responding on `127.0.0.1:11434`.
- Confirmed `llama3:latest` is installed.
- Explained that `bind: address already in use` means another Ollama server is already listening, so the app can use the existing server.
- Confirmed CPU-only Ollama works but can be slow; a tiny generation test completed successfully but took about 58 seconds.
- Recommended short prompts, caching recommendations by slot/category, and keeping mock/rule-based fallback enabled for demo reliability.
- Updated installation notes with the `ollama serve` explanation and CPU-only performance guidance.

## Prompt 6

### User Prompt

> Take note of the rules in the agent workflow as suggested above for implementation. The next development step is to implement the backend AI service wrapper: one interface that can call Ollama via CrewAI/LiteLLM, optionally switch to OpenAI, and fall back to mock/rule-based recommendation when needed. Are there decisions I must make at this stage? At what stage are we in the implementation plan / phases after this?

### Decision / Planning Summary

- Recorded the internal agent workflow rules in the implementation plan.
- Confirmed users should not interact directly with CrewAI.
- Confirmed normal user actions should read stored/cached state instead of waiting for LLM calls.
- Identified the next implementation unit as the backend AI service wrapper with provider switching and mock fallback.

## Prompt 7

### User Prompt

> I accept recommendations 1. to 4. Complete pending in Phase 1 and Phase 2

### Decision Made

- Accepted the recommended AI behaviour:
  - Ollama-first real LLM mode.
  - Mock fallback enabled for demo safety.
  - Generate/cache recommendations by `slot + category`.
  - Keep LLM reasoning limited to video recommendation and safety review.

### Implementation Summary

- Completed Phase 1 documentation/scaffold cleanup.
- Completed Phase 2 backend core.
- Added SQLAlchemy database setup and session handling.
- Added ORM models for all project-specified tables.
- Added seed data for 9am-9pm hourly slots and Upper Body / Lower Body categories.
- Added backend status, time-slot, workout-category, and video-session read endpoints.
- Added `scripts/init_db.py` for local schema creation and seed setup.
- Added focused backend tests for Phase 2 core behaviour.

### Debug / Verification

- FastAPI `TestClient` hung in this environment, so tests were later adjusted to use `httpx.ASGITransport` for HTTP-style ASGI testing.
- Backend tests pass with `4 passed`.

## Prompt 8

### User Prompt

> 1.

### Context

The user chose option 1 from the previous recommendation: investigate and resolve the FastAPI `TestClient` issue before progressing into Phase 3.

### Debug Summary

- Reproduced the hang with a minimal FastAPI app, confirming the issue was not caused by this project's database, lifespan, or route code.
- The hang occurs inside Starlette `TestClient` through AnyIO's cross-thread portal.
- Downgrading Starlette from `1.0.0` to `0.52.1` and AnyIO from `4.13.0` to `4.9.0` did not make `TestClient` usable in this sandbox.
- `httpx.ASGITransport` works for async ASGI app testing and avoids the broken threaded portal.

### Implementation Summary

- Pinned `starlette==0.52.1` and `anyio==4.9.0` for a more stable FastAPI test/runtime stack.
- Converted current backend route handlers and database dependency to async-compatible definitions.
- Reworked Phase 2 tests to use `httpx.ASGITransport` for HTTP-style ASGI tests instead of Starlette `TestClient`.
- Verified backend tests pass and `pip check` reports no broken requirements.

## Prompt 9

### User Prompt

> do you validate email? how? If not validate, then we could keep it for future improvements.  guess access not permit dashboard/broadcast without login. yes to seed one local admin account. But what happens to it in production?  Update default admin account email and password in README.md. What it Token style, I think I am not concerned with it, choose what is best suited but document it with rationale. Member registration keep email optional. yes to Role handling.Yes to keep prototype security demo-appropriate. And yes to rest of prototype security level. Go ahead with next phase.

### Decision Summary

- Member email initially remained optional during registration; this was later superseded in Prompt 12 so member registration supports future login.
- If email is provided, it is validated with Pydantic `EmailStr` and `email-validator`.
- Dashboard and broadcast data require login; guests are limited to public status/auth routes.
- One local admin account is seeded for prototype evaluation.
- JWT bearer tokens are used for the prototype because they are simple for React/FastAPI API calls and avoid server-side sessions.
- Security remains demo-appropriate, with production hardening documented as future work.

### Implementation Summary

- Added auth schemas, security helpers, auth service functions, and seeded admin support.
- Added member registration, login, current-user, and admin-summary endpoints.
- Protected dashboard/broadcast data routes with authenticated-user guards.
- Added role-based admin restrictions.
- Updated README, installation notes, and the implementation plan with admin credentials, token rationale, email validation behaviour, and production notes.
- Added Phase 3 tests for registration, email validation, login, admin access, member restriction, and guest restriction.
- Superseded by Prompt 12: member registration now requires email.

### Debug / Refinement

- Changed the default admin email to `admin@example.com` because `.local` domains can fail strict email validation.
- Pinned `bcrypt==4.0.1` because newer bcrypt releases removed metadata that `passlib` expects, causing noisy startup warnings.

## Prompt 10

### User Prompt

> update Default local admin information README.md. Regarding harmless passlib deprecation warning, did you  install bcrypt version 4.x, not 5.x. Example dependency: bcrypt<5
> passlib ? My Codex message says rate limit resets on 5:31 pm, does this mean you won't be able to process this prompt?

### Response / Implementation Summary

- Confirmed the local environment uses `bcrypt 4.0.1` and `passlib 1.7.4`; bcrypt 5.x is not installed.
- Kept the stricter dependency pin `bcrypt==4.0.1` because it avoids compatibility warnings better than the broader `bcrypt<5` range.
- Updated README default local admin information to show the seeded environment variables, prototype-only warning, and bcrypt/passlib note.
- Clarified that the Codex rate-limit message is an account/product quota notice, not a blocker for the current processed prompt.

## Prompt 11

### User Prompt

> what are pending unresolved issues? what decision are pending to move to next phase?

### Response Summary

- Reviewed implementation plan, README, prompt log, and current worktree state.
- Identified no blocking unresolved issue for moving into Phase 4.
- Listed known non-blocking technical notes and the small Phase 4 decisions needed before implementation.

## Prompt 12

### User Prompt

> Decision regarding unresolved issue:
> Proceed to Phase 4. Authentication is acceptable for prototype use.
>
> Resolved:
> - Default admin email changed to admin@example.com.
> - bcrypt pinned to 4.0.1.
> - TestClient replaced by httpx.ASGITransport.
>
> Accepted limitations:
> - passlib Python 3.12 warning is non-blocking.
> - Production-grade auth features are deferred.
> - Member registration will require email to support future login.
> - Guest access remains separate and does not require email.
>
> Worktree has many Phase 1-3 changes, commit it. Will resolve pending decisions for Phase 4 in next prompt.

### Decision / Implementation Summary

- Recorded Phase 3 authentication as acceptable for prototype use.
- Updated member registration to require email while keeping guest access separate.
- Kept accepted limitations documented: passlib warning is non-blocking and production-grade auth is deferred.
- Prepared the Phase 1-3 worktree for commit after verification.

## Prompt 13

### User Prompt

> my last git commit : commit e5501f3b8e526967e5858e56298edb89e03e9ef1 , if this true, continue wtih git commit and push.

### Response / Implementation Summary

- Verified `e5501f3b8e526967e5858e56298edb89e03e9ef1` is the current `HEAD`.
- Confirmed Phase 1-3 changes were staged on `main`.
- Proceeded with commit and push workflow.

## Prompt 14

### User Prompt

> I agree with suggested Phase 4 default: implement reserve/cancel endpoints, enforce 20-member capacity, prevent duplicate reservations for the same member and slot, and add admin occupancy summary. Continue

### Decision / Implementation Summary

- Implemented Phase 4 slot scheduling using deterministic backend/database rules.
- Added member reservation create, list, and cancel endpoints.
- Added admin occupancy summary endpoint.
- Enforced one reservation per member per time slot.
- Enforced slot capacity using the seeded capacity value, defaulting to 20.
- Added Phase 4 tests for reserve/cancel, duplicate prevention, capacity rejection, admin occupancy, and member/admin access control.

## Prompt 15

### User Prompt

> If the unresolved issues do not obstruct next phase, keep moving. git commit after phase 5 implementation. I agree with suggestion for phase 5. proceed.

### Decision / Implementation Summary

- Proceeded to Phase 5 because the remaining issues were non-blocking.
- Implemented cached video recommendation creation through `video_sessions`.
- Added provider-aware recommendation service with a LiteLLM review hook and mock fallback for demo reliability.
- Added direct recommendation endpoint and automatic recommendation creation after reservation.
- Added tests for recommendation creation, cache reuse, reservation-triggered creation, and guest access restriction.
- Prepared to commit after Phase 5 verification.

## Prompt 16

### User Prompt

> proceed to implement phase 6 with suggestions.

### Decision / Implementation Summary

- Implemented Phase 6 feedback loop with member-only like/dislike feedback.
- Enforced that feedback requires a matching reservation for the video session.
- Allowed repeated feedback to update the existing member/video feedback record.
- Added admin feedback summary with likes, dislikes, total feedback, and score.
- Added tests for feedback create/update, invalid values, reservation requirement, admin summary, guest restriction, and member restriction.

## Prompt 17

### User Prompt

> I want to ensure this is a  Single Page Application (SPA) in React. I am fine with suggested Phase 7 scope. The landing page design could take inspiration from mock_up_fronend_page* attached, and you may use the image medium_shot_woman* attached.

### Decision / Implementation Summary

- Replaced the static frontend scaffold with a React/Vite single page application.
- Used the supplied workout image as the hero visual and adapted the provided mockup's high-contrast fitness landing style into the app entry screen.
- Added login/register, member dashboard, and admin dashboard views inside one React app shell.
- Connected the frontend to backend APIs for auth, slots, categories, reservations, video sessions, feedback, occupancy, and feedback summary.
- Added local FastAPI CORS support for the Vite dev server.
- Verified the frontend production build and backend test suite.

## Prompt 18

### User Prompt

> I visited Frontend SPA. I selected a timeslot, appears in reservation. In workout broadcast I see a title of workout, it says Mock. The question is , how do I play the video. Is playing the video feature implemented?

### Response Summary

- Clarified that video playback is not implemented yet.
- Explained that `Mock` means the backend used the safe mock/rule-based recommendation fallback, not a real YouTube video.
- Identified the next implementation step as real YouTube video lookup plus frontend embedded playback.

## Prompt 19

### User Prompt

> Here are some page layout improvement suggestions. 1) The signin box is partially hidden at the bottom. I suggest the sign in appear on the right side, below the menu options [slot broadcast feedback] in full screen mode, as a vertical box, with email and password widgets stacked vertically. SImilarly if Register is selected, all input widgets are placed vertically on top of each other in logical order. In half screen mode, the sign in box could be displayed at the bottom.  For the purpose of demonstration, include a time slot option 'demo now' which begin 2 seconds after selection. And ofcourse implement feature suggested above. We test this first before moving on to fine tuning other features, layouts, and resolving pending issues.

### Decision / Implementation Summary

- Moved the sign-in/register panel into the right side of the hero area for desktop.
- Kept the auth panel stacked below the hero copy on smaller screens.
- Changed login and registration inputs to a single vertical form flow.
- Added a `Demo now` slot option that starts a demo reservation after two seconds.
- Added embedded YouTube playback in workout broadcast cards.
- Updated mock fallback recommendations to use playable demo YouTube IDs while keeping provider labelled as `mock`.

## Prompt 20

### User Prompt

> why is video unavailable on our application page, but when I click on the play on youtube link, it does open youtube link in a different tab and play. The idea is it should play in our page.

### Debug / Implementation Summary

- Explained that YouTube can allow playback on YouTube while blocking third-party embedded playback.
- Updated the backend recommendation service to use YouTube Data API search with `videoEmbeddable=true` when a `YOUTUBE_API_KEY` is available.
- Kept mock fallback for no-network/no-key demo safety.
- Changed frontend embeds to use `youtube-nocookie.com/embed/...` with an `origin` parameter.
- Hardened the YouTube provider path so network/DNS failure falls back to mock recommendation instead of breaking reservation flows.

## Prompt 21

### User Prompt

> suggestions - 1) if a video was embeddable, and it played, keep track of that video, because in the future if a new embedable video is not available, you could fallback to cached video. 2) Always attempt to pull a new video first, before fallback to cache.
> Make a DEBUG flag in config.py such that if True, it prints the debug for frontend and backend -
> The frontend now logs the full demo flow in the browser console: refresh, reservation request, backend recommendation refresh, loaded videos, provider, YouTube ID, whether the ID is still mock, and the embed URL. I’m building and testing now.

### Decision / Implementation Summary

- Added a shared backend `DEBUG` setting and exposed it through `/api/status`.
- Changed backend recommendation debug printing so terminal `[FitHub AI]` lines print only when `DEBUG=true`.
- Updated the frontend to load the backend debug flag and only print browser console debug logs when debugging is enabled.
- Updated recommendation selection to try a fresh YouTube embeddable search first, then reuse a previously approved cached embeddable video, then fall back to mock recommendations.
- Added backend tests for cached embeddable fallback and fresh-search-before-cache behavior.

## Prompt 22

### User Prompt

> start to log prompt. here are some observations in the page that needs to be rectified.
> 1. I didn't make reservation for 9:00 AM - 10:00 AM, but it shows in Reservation box.
> 2. volume is audible in the host machine, is it because I am in the VMM?
> 3. considering I am in the vmm, can next user login to frontend url? give it a domain name,  such that it is accessible from another computer.
> 4. when I minimize full screen video, then resume video it starts from beginning, I want it to continue from where it left off. All participants must view same video continuity.
> 5.Option for user to exit session. If exit they cannot get back into the same session.
> 6. missing features - Guest login.
> 7. why are slots, broadcast, feedback Menu options unresponsive?
> 8. When Like / Dislike clicked, icon change color.
> 9. Member or login name font color white, so it is visible against dark red background.
> 10. remove Resume broadcast link in admin dashboard?
> 11. Is the agent able to check if the video loaded is playing? If it doesn't play in 5 seconds, pick another new video, again if it doesn't play, then play a cached video. Only cache new videos that play.

### Decision / Implementation Summary

- Re-enabled prompt logging as requested.
- Began immediate UI fixes for navigation, guest preview, feedback state styling, visible user identity, admin broadcast-chip hiding, and minimize-without-unmounting.
- Identified shared video continuity and playback-health validation as a larger broadcast/player phase requiring shared backend session state and YouTube iframe player events.

## Prompt 23

### User Prompt

> log this prompt. previously it taking longer time to start video, but now it is showing video unavailable. The broadcast box should be empty, not have a previously loaded video thumbnail, clear the video. Load video only when user select time slot, in this case Demo slot and enter. Currently you have widget in red background to display Demo starts automatically overlaid on Reserve a workout box. I think we could have a dedicated box between Reserve a workout and Workout broadcast, to display informative messages such as 'Demo will start now', or if it still loading video or looking for it, give that information. Remove Guest login options and related code and update this in documentation if already mentioned.

### Decision / Implementation Summary

- Removed guest-preview login UI and related frontend code from the SPA.
- Updated README language so the prototype is described as visitor landing access plus authenticated member/admin workflows.
- Changed the member dashboard so the broadcast panel stays empty until an active broadcast is started.
- Removed the embedded preview player from the broadcast card to avoid stale thumbnails or old unavailable videos before a new session starts.
- Added a dedicated session-status panel between reservation information and the broadcast area for demo-start, loading, and recommendation messages.
- Removed the red `Demo starts automatically` button text from the reservation box.

## Prompt 24

### User Prompt

> ok that being the case, I will abandon the idea of using CrewAI, implement the video curator agent suggestions pending implementation, document the prompt, and update relavant documents. cleanup documentation that incorrectly assumes or suggests use of CrewAI.

### Decision / Implementation Summary

- Abandoned CrewAI for the current prototype.
- Kept deterministic backend services as the primary architecture for reliability, speed, and testability.
- Implemented a code-based Video Curator service instead of a CrewAI agent.
- Added `video_cache_entries` to track confirmed playable videos, play count, replacement status, safety notes, and curator summaries.
- Updated recommendation selection to prefer confirmed playable cached videos before live YouTube or mock fallback.
- Added least-played video selection and marked cached videos for replacement after three plays.
- Added frontend playback confirmation integration so only videos that actually play can become confirmed cache entries.
- Added admin video-cache endpoints and daily scheduler configuration.
- Removed CrewAI from Python requirements and `.env.example`.
- Updated README, installation notes, and implementation plan to remove misleading CrewAI assumptions.

## Prompt 25

### User Prompt

> Demo time slot vs regular time slot behaviour varies. Regular time slot allows user to change workout category for an already reserved time slot. When a regular time slot is Reserved (Reserve slot), the Session status must only indicate a time slot a category has been reserved. The video playback session does not begin until the time has arrived, so no video curator activity should take place, which should only take place if the user is logged in and the current system time is within the reserved time slot window.
> You previously mention 'If you first reserved the demo slot as Upper Body, then later selected Lower Body, the backend said “already reserved this slot.” --> I believe this applied to Demo time slot. Allow Demo time slot to be a special, unlike other time slots, if a user has reserved Upperbody, the video loads and plays, say user exits session, clear the session and video associated with Demo time slot, allowing user to select another category and reserve again.

### Decision / Implementation Summary

- Changed reservation behavior so regular future-slot reservations only store the selected time slot and workout category.
- Removed automatic backend video recommendation creation from the reservation endpoint.
- Kept `Demo time slot` as the immediate-play exception for local demos.
- Added frontend logic so regular slots only prepare/start video when the current system hour is inside the reserved slot window.
- Kept the existing category-update behavior for an already reserved slot so a member can change workout category without creating a duplicate reservation.
- Updated tests and documentation to reflect reservation-only regular slots versus immediate demo playback.

## Prompt 26

### User Prompt

> add another workout category 'Cardio', video curator needs to update video cache, same rules apply.

### Decision / Implementation Summary

- Added `Cardio` as a seeded workout category.
- Added a Cardio mock fallback recommendation for no-key/no-network demos.
- Added a frontend Cardio fallback video ID for mock playback.
- Video Curator cache logic applies automatically because it iterates over all active workout categories.
- Updated backend tests and implementation plan references from two categories to three categories.

## Prompt 27

### User Prompt

> I notice when I have not reserved regular time slot, 9 a.m to 10 a.m time slot appears in Your Reservation, the close proximity of this time slot to Demo time slot could offer a clue. But be assured the user did not select the regular time slot at all.

### Decision / Implementation Summary

- Confirmed the bug: the demo flow was borrowing the first regular slot ID, so demo reservations appeared as `9:00 AM - 10:00 AM`.
- Added an explicit seeded `Demo time slot` with `is_demo=true`.
- Kept regular 9am-9pm slots as normal non-demo slots.
- Updated frontend logic so the demo option uses the explicit demo slot and the regular dropdown filters demo out.
- Updated time-slot and occupancy schemas/tests to include the demo flag.
