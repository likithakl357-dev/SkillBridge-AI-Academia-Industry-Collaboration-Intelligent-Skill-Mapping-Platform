from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from pathlib import Path
import json

from .database import init_db, get_conn
from .security import hash_password, verify_password, create_token, read_token
from .matching import match_opportunity

app = FastAPI(title="SkillBridge AI", version="1.0.0",
              description="Academia–Industry Collaboration, Skill Mapping, Internships and Placement Portal")
BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=8)
    role: str
    department: str = ""

class LoginIn(BaseModel):
    email: str
    password: str

class SkillIn(BaseModel):
    name: str
    level: int = Field(ge=1, le=5)
    evidence: str = ""
    evidence_type: str = "Self-reported"

class OpportunityIn(BaseModel):
    title: str
    company: str
    kind: str = "Internship"
    description: str = ""
    required_skills: list[str]
    location: str = "Remote"
    eligibility: str = "Open to students"

class StatusIn(BaseModel):
    status: str

def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please sign in.")
    data = read_token(authorization[7:])
    if not data:
        raise HTTPException(401, "Session expired. Please sign in again.")
    with get_conn() as db:
        user = db.execute("SELECT id,name,email,role,department FROM users WHERE id=?", (int(data["sub"]),)).fetchone()
    if not user:
        raise HTTPException(401, "Account not found.")
    return dict(user)

def require_role(user, *roles):
    if user["role"] not in roles:
        raise HTTPException(403, "Your account role cannot perform this action.")
    return user

def seed():
    with get_conn() as db:
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            demos = [
                ("Aarav Student","student@demo.com","Student@123","student","Computer Science"),
                ("NovaTech HR","industry@demo.com","Industry@123","industry","Talent Acquisition"),
                ("Dr. Meera Faculty","faculty@demo.com","Faculty@123","academician","Electronics"),
                ("Campus Admin","institution@demo.com","Admin@12345","institution","Placement Cell")
            ]
            for name,email,pw,role,dept in demos:
                db.execute("INSERT INTO users(name,email,password_hash,role,department) VALUES(?,?,?,?,?)",
                           (name,email,hash_password(pw),role,dept))
            student_id = db.execute("SELECT id FROM users WHERE email='student@demo.com'").fetchone()[0]
            for name,level,evidence,etype,verified in [
                ("Python",4,"Built a data analysis project","Project",1),
                ("SQL",3,"Completed database coursework","Coursework",0),
                ("Communication",4,"Team presentation","Assessment",1),
                ("React",2,"Personal portfolio prototype","Project",0)
            ]:
                db.execute("INSERT INTO skills(user_id,name,level,evidence,evidence_type,verified) VALUES(?,?,?,?,?,?)",
                           (student_id,name,level,evidence,etype,verified))
            opps = [
                ("Python Data Engineering Intern","NovaTech Labs","Internship","Work with ETL pipelines and structured datasets.",["Python","SQL","Data Engineering"],"Remote","Students with basic Python and SQL"),
                ("Frontend Developer Intern","PixelWorks","Internship","Build accessible web interfaces with a product team.",["React","JavaScript","CSS"],"Hybrid · Chennai","Undergraduate students"),
                ("Junior Data Analyst","InsightBridge","Entry-level Job","Create reports and derive insights from business data.",["Python","SQL","Communication"],"Remote","Graduates and final-year students"),
                ("Faculty Industry Immersion","NovaTech Labs","Faculty Program","Short-term industry exposure for faculty members.",["Data Engineering","Cloud"],"Chennai","Academicians")
            ]
            for title,company,kind,desc,skills,loc,elig in opps:
                db.execute("INSERT INTO opportunities(title,company,kind,description,required_skills,location,eligibility,posted_by) VALUES(?,?,?,?,?,?,?,?)",
                           (title,company,kind,desc,json.dumps(skills),loc,elig,None))
            for title,skill,provider,url in [
                ("Python for Data Workflows","Python","GUVI","https://www.guvi.in/"),
                ("SQL Fundamentals","SQL","Khan Academy","https://www.khanacademy.org/"),
                ("React Getting Started","React","React","https://react.dev/learn"),
                ("Cloud Foundations","Cloud","AWS Skill Builder","https://skillbuilder.aws/")
            ]:
                db.execute("INSERT INTO learning(title,skill,provider,url) VALUES(?,?,?,?)",(title,skill,provider,url))
            db.commit()

@app.on_event("startup")
def startup():
    init_db()
    seed()

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"status":"ok","service":"SkillBridge AI"}

@app.post("/api/register")
def register(data: RegisterIn):
    if data.role not in ["student","industry","academician","institution"]:
        raise HTTPException(400,"Choose a valid account role.")
    with get_conn() as db:
        try:
            cur = db.execute("INSERT INTO users(name,email,password_hash,role,department) VALUES(?,?,?,?,?)",
                             (data.name.strip(),data.email.lower().strip(),hash_password(data.password),data.role,data.department.strip()))
            db.commit()
            return {"token":create_token(cur.lastrowid,data.role)}
        except Exception:
            raise HTTPException(409,"An account with this email may already exist.")

@app.post("/api/login")
def login(data: LoginIn):
    with get_conn() as db:
        user = db.execute("SELECT * FROM users WHERE email=?",(data.email.lower().strip(),)).fetchone()
    if not user or not verify_password(data.password,user["password_hash"]):
        raise HTTPException(401,"Incorrect email or password.")
    return {"token":create_token(user["id"],user["role"])}

@app.get("/api/me")
def me(user=Depends(current_user)):
    return user

@app.get("/api/skills")
def get_skills(user=Depends(current_user)):
    with get_conn() as db:
        rows = db.execute("SELECT * FROM skills WHERE user_id=? ORDER BY name",(user["id"],)).fetchall()
    return [dict(r) for r in rows]

@app.post("/api/skills")
def add_skill(data: SkillIn, user=Depends(current_user)):
    require_role(user,"student")
    with get_conn() as db:
        try:
            db.execute("INSERT INTO skills(user_id,name,level,evidence,evidence_type) VALUES(?,?,?,?,?)",
                       (user["id"],data.name.strip(),data.level,data.evidence.strip(),data.evidence_type))
            db.commit()
        except Exception:
            raise HTTPException(409,"That skill is already in your Skill Passport.")
    return {"message":"Skill added to your Skill Passport."}

@app.get("/api/opportunities")
def opportunities(user=Depends(current_user)):
    with get_conn() as db:
        rows = db.execute("SELECT * FROM opportunities ORDER BY created_at DESC").fetchall()
        skills = [dict(r) for r in db.execute("SELECT * FROM skills WHERE user_id=?",(user["id"],)).fetchall()]
        applied = {r["opportunity_id"] for r in db.execute("SELECT opportunity_id FROM applications WHERE user_id=?",(user["id"],)).fetchall()}
    result=[]
    for row in rows:
        item=dict(row); required=json.loads(item["required_skills"])
        item["required_skills"]=required
        item["match"]=match_opportunity(skills,required) if user["role"]=="student" else None
        item["applied"]=item["id"] in applied
        result.append(item)
    return result

@app.post("/api/opportunities")
def create_opportunity(data: OpportunityIn, user=Depends(current_user)):
    require_role(user,"industry","academician")
    with get_conn() as db:
        cur=db.execute("INSERT INTO opportunities(title,company,kind,description,required_skills,location,eligibility,posted_by) VALUES(?,?,?,?,?,?,?,?)",
            (data.title,data.company,data.kind,data.description,json.dumps(data.required_skills),data.location,data.eligibility,user["id"]))
        db.commit()
    return {"id":cur.lastrowid,"message":"Opportunity published."}

@app.post("/api/apply/{opportunity_id}")
def apply(opportunity_id: int, user=Depends(current_user)):
    require_role(user,"student")
    with get_conn() as db:
        if not db.execute("SELECT id FROM opportunities WHERE id=?",(opportunity_id,)).fetchone():
            raise HTTPException(404,"Opportunity not found.")
        try:
            db.execute("INSERT INTO applications(user_id,opportunity_id) VALUES(?,?)",(user["id"],opportunity_id))
            db.commit()
        except Exception:
            raise HTTPException(409,"You have already applied.")
    return {"message":"Application submitted."}

@app.get("/api/applications")
def applications(user=Depends(current_user)):
    with get_conn() as db:
        if user["role"] in ["industry","academician"]:
            rows=db.execute("""SELECT a.id,a.status,a.created_at,u.name AS student,o.title,o.company
                FROM applications a JOIN users u ON u.id=a.user_id JOIN opportunities o ON o.id=a.opportunity_id
                WHERE o.posted_by=? ORDER BY a.created_at DESC""",(user["id"],)).fetchall()
        elif user["role"]=="institution":
            rows=db.execute("""SELECT a.id,a.status,a.created_at,u.name AS student,o.title,o.company
                FROM applications a JOIN users u ON u.id=a.user_id JOIN opportunities o ON o.id=a.opportunity_id
                ORDER BY a.created_at DESC""").fetchall()
        else:
            rows=db.execute("""SELECT a.id,a.status,a.created_at,o.title,o.company,o.kind
                FROM applications a JOIN opportunities o ON o.id=a.opportunity_id
                WHERE a.user_id=? ORDER BY a.created_at DESC""",(user["id"],)).fetchall()
    return [dict(r) for r in rows]

@app.patch("/api/applications/{application_id}")
def update_application(application_id: int, data: StatusIn, user=Depends(current_user)):
    require_role(user,"industry","institution")
    if data.status not in ["Applied","Under Review","Shortlisted","Interview","Selected","Rejected"]:
        raise HTTPException(400,"Invalid application status.")
    with get_conn() as db:
        if user["role"]=="industry":
            row=db.execute("""SELECT a.id FROM applications a JOIN opportunities o ON o.id=a.opportunity_id
                              WHERE a.id=? AND o.posted_by=?""",(application_id,user["id"])).fetchone()
        else:
            row=db.execute("SELECT id FROM applications WHERE id=?",(application_id,)).fetchone()
        if not row: raise HTTPException(404,"Application not found.")
        db.execute("UPDATE applications SET status=? WHERE id=?",(data.status,application_id)); db.commit()
    return {"message":"Application status updated."}

@app.get("/api/learning")
def learning(user=Depends(current_user)):
    with get_conn() as db:
        rows=db.execute("SELECT * FROM learning ORDER BY skill").fetchall()
    return [dict(r) for r in rows]

@app.get("/api/analytics")
def analytics(user=Depends(current_user)):
    require_role(user,"institution")
    with get_conn() as db:
        students=db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        apps=db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        opps=db.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        status=db.execute("SELECT status,COUNT(*) AS total FROM applications GROUP BY status").fetchall()
        skillrows=db.execute("SELECT name,COUNT(*) AS total FROM skills GROUP BY name ORDER BY total DESC LIMIT 8").fetchall()
    return {"students":students,"applications":apps,"opportunities":opps,
            "statuses":[dict(x) for x in status],"skills":[dict(x) for x in skillrows]}

@app.get("/api/portfolio")
def portfolio(user=Depends(current_user)):
    with get_conn() as db:
        skills=[dict(x) for x in db.execute("SELECT name,level,evidence,evidence_type,verified FROM skills WHERE user_id=?",(user["id"],)).fetchall()]
        apps=[dict(x) for x in db.execute("""SELECT o.title,o.company,o.kind,a.status,a.created_at
            FROM applications a JOIN opportunities o ON o.id=a.opportunity_id WHERE a.user_id=?""",(user["id"],)).fetchall()]
    return {"profile":user,"skills":skills,"applications":apps}
