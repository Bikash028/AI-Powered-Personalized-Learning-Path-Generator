from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from schemas import StudentCreate, PerformanceCreate
from ml_model import predict_weakness
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "AI Learning Path Generator Running"}

@app.post("/add_student/")
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    new_student = models.Student(name=student.name, email=student.email)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.post("/add_performance/")
def add_performance(data: PerformanceCreate, db: Session = Depends(get_db)):
    performance = models.TopicPerformance(
        student_id=data.student_id,
        topic=data.topic,
        score=data.score,
        total=data.total
    )
    db.add(performance)
    db.commit()
    return {"message": "Performance added"}

# Weakness analysis and learning path generation endpoints would go here, using the stored data to analyze and generate paths based on student performance.

@app.get("/analyze/{student_id}")
def analyze_student(student_id: int, db: Session = Depends(get_db)):
    records = db.query(models.TopicPerformance).filter(
        models.TopicPerformance.student_id == student_id
    ).all()

    result = []

    for r in records:
        percentage = (r.score / r.total) * 100

        status = predict_weakness(percentage)

        result.append({
            "topic": r.topic,
            "percentage": percentage,
            "status": status
        })

    return {"analysis": result}



RESOURCES = {
    "Sorting": {
        "Beginner": "https://youtube.com/sorting-basic",
        "Intermediate": "https://youtube.com/sorting-advanced"
    },
    "Graph": {
        "Beginner": "https://youtube.com/graph-basic",
        "Intermediate": "https://youtube.com/graph-advanced"
    }
}

@app.get("/recommend/{student_id}")
def recommend(student_id: int, db: Session = Depends(get_db)):
    records = db.query(models.TopicPerformance).filter(
        models.TopicPerformance.student_id == student_id
    ).all()

    recommendations = []

    for r in records:
        percentage = (r.score / r.total) * 100

        if r.topic in RESOURCES:
            if percentage < 40:
                level = "Beginner"
            else:
                level = "Intermediate"

            recommendations.append({
                "topic": r.topic,
                "recommended_video": RESOURCES[r.topic][level]
            })

    return {"recommendations": recommendations}

@app.post("/track_progress/")
def track_progress(student_id: int, topic: str, week: int, percentage: float, db: Session = Depends(get_db)):
    progress = models.Progress(
        student_id=student_id,
        topic=topic,
        week=week,
        percentage=percentage
    )
    db.add(progress)
    db.commit()
    return {"message": "Progress tracked successfully"}

@app.get("/progress/{student_id}")
def get_progress(student_id: int, db: Session = Depends(get_db)):
    records = db.query(models.Progress).filter(
        models.Progress.student_id == student_id
    ).all()

    improvement_data = {}

    for r in records:
        if r.topic not in improvement_data:
            improvement_data[r.topic] = []

        improvement_data[r.topic].append(r.percentage)

    final_output = []

    for topic, percentages in improvement_data.items():
        improvement = percentages[-1] - percentages[0] if len(percentages) > 1 else 0

        final_output.append({
            "topic": topic,
            "scores": percentages,
            "improvement": improvement
        })

    return {"progress_analysis": final_output}


@app.get("/generate_plan/{student_id}")
def generate_learning_plan(student_id: int, db: Session = Depends(get_db)):
    
    records = db.query(models.TopicPerformance).filter(
        models.TopicPerformance.student_id == student_id
    ).all()

    if not records:
        return {"message": "No performance data found"}

    # Calculate percentage and sort by lowest score
    topic_data = []

    for r in records:
        percentage = (r.score / r.total) * 100
        topic_data.append({
            "topic": r.topic,
            "percentage": percentage
        })

    # Sort weakest first
    topic_data.sort(key=lambda x: x["percentage"])

    weekly_plan = []
    week_number = 1

    for topic in topic_data:
        if topic["percentage"] < 60:

            level = "Beginner" if topic["percentage"] < 40 else "Intermediate"

            topic_name = topic["topic"].capitalize()
            resource = RESOURCES.get(topic_name, {}).get(level, "No resource found")

            weekly_plan.append({
                "week": week_number,
                "focus_topic": topic["topic"],
                "current_score": topic["percentage"],
                "recommended_video": resource,
                "practice_problems": 10 if level == "Beginner" else 15
            })

            week_number += 1

    if not weekly_plan:
        return {"message": "Student performing well. Focus on advanced practice."}

    return {"learning_plan": weekly_plan}
