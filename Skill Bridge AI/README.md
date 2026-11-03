# SkillBridge AI
**Hackathon Problem 26044 — Portal for Academia–Industry Collaboration for Skill Mapping, Internships and Placement**

SkillBridge AI is a responsive, role-based web application prototype connecting students, industry partners, academicians and institutions.

## Core innovation: Skill Passport + Explainable Matching
Each student's Skill Passport stores a skill, proficiency level and supporting evidence description (project, certification, coursework, assessment or self-reported). The opportunity matcher compares required skills with the passport and displays:
- a transparent percentage based on required skills present;
- matched skills;
- missing skills;
- a plain-language explanation of the match.

This is an explainable baseline, not a trained AI model. It is intentionally transparent and can be extended with semantic matching and verified evidence workflows.

## Implemented modules
- Role-based registration and sign-in: student, industry, academician, institution.
- Student Skill Passport with evidence descriptions and proficiency levels.
- Opportunity board for internships, entry-level jobs, live projects, apprenticeships, faculty programs, FDPs and research collaboration.
- Explainable opportunity matching and skill-gap display.
- Student applications and application status tracking.
- Industry/academician opportunity publishing and applicant status updates.
- Institution analytics for student count, opportunities, application pipeline and recorded skill signals.
- Digital portfolio view with print / Save PDF.
- Learning resource suggestions.
- SQLite database and demo seed data.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

API docs: http://127.0.0.1:8000/docs

## Demo accounts
| Role | Email | Password |
|---|---|---|
| Student | student@demo.com | Student@123 |
| Industry | industry@demo.com | Industry@123 |
| Academician | faculty@demo.com | Faculty@123 |
| Institution | institution@demo.com | Admin@12345 |

The database seeds these accounts and sample opportunities on first launch. Delete `skillbridge.db` to reset local demo data.

## Deploy to Render
1. Push this project folder to a GitHub repository.
2. In Render, choose **New → Blueprint** and connect the repository. Render reads `render.yaml`.
3. Wait for build and deployment.
4. Test `/api/health`, then sign in with a demo account.
5. Change demo passwords / disable public demo accounts before public production use.

The Render blueprint provisions a persistent disk for SQLite. For a larger production deployment, use managed PostgreSQL and object storage for uploaded evidence files.

## Environment variables
- `SECRET_KEY`: long random secret used to sign session tokens. Set a unique production value.
- `DATABASE_PATH`: SQLite database path. Defaults to `./skillbridge.db`.

## Important prototype limitations / next steps
This is a runnable hackathon MVP, not a production-hardened recruitment system:
- Skill evidence is described by the student; the current prototype does not verify uploaded certificates or external credentials.
- Institution analytics are aggregate counts, but fine-grained institution tenancy and privacy controls need to be implemented before real institutional use.
- Add email verification, password reset, rate limiting, audit logs, file scanning, consent and retention controls before production.
- Replace the transparent skill-overlap baseline with a validated recommendation model only after collecting consented, representative data.
- Add institution review workflow to verify evidence and update the `verified` flag.
- Use PostgreSQL and cloud object storage for scale.

## Project structure
```text
skillbridge-ai/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── security.py
│   ├── matching.py
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```
