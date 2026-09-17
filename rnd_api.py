"""
R&D Cross-Module API - FastAPI Application
Provides RESTful API endpoints for interlinked R&D modules with hardware dependency checking
and risk/compliance triggers for stage gates
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
import uuid

# Import database models
from rnd_database_schema import (
    Base, Product, Task, Sprint, HardwarePrototype, Component, ProductComponent,
    Risk, TeamMember, TeamAllocation, ComplianceRecord,
    TaskStatus, HardwareStatus, RiskLevel, RiskStatus, ComplianceStatus,
    StageGate, CurrentStage, get_database_url
)

# FastAPI application
app = FastAPI(
    title="R&D Engineering Management API",
    description="Cross-module API for interlinked R&D management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models for Request/Response

class ProductBase(BaseModel):
    product_name: str
    product_type: str
    current_stage: str = "Requirements"
    stage_gate: str = "Stage 1"
    start_date: date
    target_date: date
    team_lead: Optional[str] = None
    completion_percentage: int = 0
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    product_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    task_name: str
    task_type: str
    status: str = "To Do"
    assigned_to: Optional[str] = None
    hardware_dependent: bool = False
    required_hardware_id: Optional[str] = None
    required_component_id: Optional[str] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    actual_hours: float = 0
    priority: str = "Medium"
    description: Optional[str] = None
    sprint_id: Optional[str] = None


class TaskCreate(TaskBase):
    product_id: str


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    actual_hours: Optional[float] = None
    description: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    task_id: str
    product_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FullProductDashboard(BaseModel):
    """Unified payload combining PDLC status, active sprint tasks, linked hardware prototypes, and component stock status"""
    product: ProductResponse
    pdlc_status: Dict[str, Any]
    active_sprint_tasks: List[TaskResponse]
    hardware_prototypes: List[Dict[str, Any]]
    component_stock_status: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    compliance_status: List[Dict[str, Any]]
    stage_gate_blockers: List[str]


# Helper Functions

def generate_product_id() -> str:
    """Generate unique product ID"""
    return f"PDLC-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def check_hardware_dependency(db: Session, task: Task) -> Dict[str, Any]:
    """
    Check if hardware dependencies are met for a task
    Returns dict with status and details
    """
    if not task.hardware_dependent:
        return {"dependency_met": True, "message": "No hardware dependency"}

    result = {"dependency_met": False, "message": "", "details": {}}

    # Check hardware prototype dependency
    if task.required_hardware_id:
        hardware = db.query(HardwarePrototype).filter(
            HardwarePrototype.hardware_id == task.required_hardware_id
        ).first()
        if hardware:
            result["details"]["hardware"] = {
                "hardware_id": hardware.hardware_id,
                "status": hardware.status.value,
                "bringup_status": hardware.bringup_status,
                "available": hardware.status in [HardwareStatus.PROTOTYPE, HardwareStatus.PRODUCTION]
            }
            if hardware.status in [HardwareStatus.PROTOTYPE, HardwareStatus.PRODUCTION]:
                result["dependency_met"] = True
                result["message"] = "Hardware prototype available"
            else:
                result["message"] = f"Hardware status: {hardware.status.value}"

    # Check component dependency
    if task.required_component_id:
        component = db.query(Component).filter(
            Component.component_id == task.required_component_id
        ).first()
        if component:
            result["details"]["component"] = {
                "component_id": component.component_id,
                "component_name": component.component_name,
                "current_stock": component.current_stock,
                "min_stock_level": component.min_stock_level,
                "status": component.status.value,
                "available": component.current_stock > component.min_stock_level
            }
            if component.current_stock > component.min_stock_level:
                result["dependency_met"] = True
                result["message"] = "Component stock sufficient"
            else:
                result["message"] = f"Component stock insufficient: {component.current_stock} vs {component.min_stock_level}"

    return result


def check_stage_gate_blockers(db: Session, product: Product) -> List[str]:
    """
    Check for blockers that prevent stage gate advancement
    Returns list of blocking issues
    """
    blockers = []

    # Check for high/critical risks
    high_risks = db.query(Risk).filter(
        Risk.product_id == product.product_id,
        Risk.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
        Risk.status != RiskStatus.RESOLVED
    ).all()

    for risk in high_risks:
        blockers.append(f"High/Critical Risk: {risk.risk_name} ({risk.risk_level.value})")

    # Check for missing compliance certifications
    current_stage = product.current_stage.value
    required_compliance = db.query(ComplianceRecord).filter(
        ComplianceRecord.product_id == product.product_id,
        ComplianceRecord.required_for_stage == product.stage_gate.value,
        ComplianceRecord.is_blocking == True
    ).all()

    for cert in required_compliance:
        if cert.status != ComplianceStatus.PASSED:
            blockers.append(f"Compliance Required: {cert.certification_name} - Status: {cert.status.value}")

    # Check for incomplete critical tasks
    incomplete_critical_tasks = db.query(Task).filter(
        Task.product_id == product.product_id,
        Task.priority == "Critical",
        Task.status != TaskStatus.DONE
    ).all()

    for task in incomplete_critical_tasks:
        blockers.append(f"Critical Task Incomplete: {task.task_name}")

    return blockers


# API Endpoints

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "R&D Engineering Management API",
        "version": "1.0.0",
        "endpoints": {
            "products": "/api/v1/products",
            "full_dashboard": "/api/v1/products/{product_id}/full-dashboard",
            "tasks": "/api/v1/tasks",
            "task_status": "/api/v1/tasks/{task_id}/status"
        }
    }


@app.get("/api/v1/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Get all products"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get specific product by ID"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/v1/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create new product"""
    product_id = generate_product_id()
    db_product = Product(
        product_id=product_id,
        **product.dict()
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/api/v1/products/{product_id}/full-dashboard", response_model=FullProductDashboard)
def get_full_product_dashboard(product_id: str, db: Session = Depends(get_db)):
    """
    Returns a unified payload combining PDLC status, active sprint tasks,
    linked hardware prototypes, and component stock status
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # PDLC Status
    pdlc_status = {
        "current_stage": product.current_stage.value,
        "stage_gate": product.stage_gate.value,
        "completion_percentage": product.completion_percentage,
        "start_date": product.start_date.isoformat(),
        "target_date": product.target_date.isoformat(),
        "team_lead": product.team_lead
    }

    # Active Sprint Tasks
    active_sprint_tasks = db.query(Task).filter(
        Task.product_id == product_id,
        Task.status.in_([TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.CODE_REVIEW, TaskStatus.HARDWARE_TESTING])
    ).all()

    task_responses = []
    for task in active_sprint_tasks:
        task_dict = {
            "id": task.id,
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "status": task.status.value,
            "assigned_to": task.assigned_to,
            "hardware_dependent": task.hardware_dependent,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority,
            "sprint_id": task.sprint_id
        }
        task_responses.append(TaskResponse(**task_dict))

    # Hardware Prototypes
    hardware_prototypes = db.query(HardwarePrototype).filter(
        HardwarePrototype.product_id == product_id
    ).all()

    hw_responses = []
    for hw in hardware_prototypes:
        hw_dict = {
            "hardware_id": hw.hardware_id,
            "hardware_name": hw.hardware_name,
            "hardware_type": hw.hardware_type,
            "status": hw.status.value,
            "pcb_status": hw.pcb_status,
            "bringup_status": hw.bringup_status,
            "revision": hw.revision,
            "quantity": hw.quantity
        }
        hw_responses.append(hw_dict)

    # Component Stock Status
    product_components = db.query(ProductComponent).filter(
        ProductComponent.product_id == product_id
    ).all()

    component_responses = []
    for pc in product_components:
        component = db.query(Component).filter(
            Component.component_id == pc.component_id
        ).first()
        if component:
            comp_dict = {
                "component_id": component.component_id,
                "component_name": component.component_name,
                "current_stock": component.current_stock,
                "min_stock_level": component.min_stock_level,
                "max_stock_level": component.max_stock_level,
                "status": component.status.value,
                "quantity_required": pc.quantity_required,
                "quantity_allocated": pc.quantity_allocated,
                "is_critical": pc.is_critical,
                "stock_sufficient": component.current_stock >= pc.quantity_required
            }
            component_responses.append(comp_dict)

    # Risks
    risks = db.query(Risk).filter(Risk.product_id == product_id).all()
    risk_responses = []
    for risk in risks:
        risk_dict = {
            "risk_id": risk.risk_id,
            "risk_name": risk.risk_name,
            "risk_type": risk.risk_type,
            "risk_level": risk.risk_level.value,
            "status": risk.status.value,
            "probability": risk.probability,
            "impact": risk.impact
        }
        risk_responses.append(risk_dict)

    # Compliance Status
    compliance_records = db.query(ComplianceRecord).filter(
        ComplianceRecord.product_id == product_id
    ).all()

    compliance_responses = []
    for cert in compliance_records:
        cert_dict = {
            "certification_id": cert.certification_id,
            "certification_type": cert.certification_type,
            "certification_name": cert.certification_name,
            "status": cert.status.value,
            "required_for_stage": cert.required_for_stage,
            "is_blocking": cert.is_blocking,
            "test_date": cert.test_date.isoformat() if cert.test_date else None,
            "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None
        }
        compliance_responses.append(cert_dict)

    # Stage Gate Blockers
    stage_gate_blockers = check_stage_gate_blockers(db, product)

    return FullProductDashboard(
        product=ProductResponse.from_orm(product),
        pdlc_status=pdlc_status,
        active_sprint_tasks=task_responses,
        hardware_prototypes=hw_responses,
        component_stock_status=component_responses,
        risks=risk_responses,
        compliance_status=compliance_responses,
        stage_gate_blockers=stage_gate_blockers
    )


@app.get("/api/v1/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, product_id: Optional[str] = None):
    """Get all tasks, optionally filtered by product"""
    query = db.query(Task)
    if product_id:
        query = query.filter(Task.product_id == product_id)
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get specific task by ID"""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/v1/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create new task"""
    task_id = generate_task_id()
    db_task = Task(
        task_id=task_id,
        **task.dict()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.patch("/api/v1/tasks/{task_id}/status")
def update_task_status(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """
    Update task status with automatic hardware dependency checking
    Automatically checks hardware dependencies before allowing a task to move to "In Progress"
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if trying to move to In Progress
    if task_update.status == "In Progress" and task.status != "In Progress":
        # Check hardware dependencies
        dependency_check = check_hardware_dependency(db, task)

        if not dependency_check["dependency_met"]:
            return {
                "success": False,
                "message": "Cannot move task to In Progress - hardware dependency not met",
                "dependency_check": dependency_check,
                "current_status": task.status.value
            }

    # Update task fields
    if task_update.status:
        task.status = TaskStatus(task_update.status)
    if task_update.assigned_to:
        task.assigned_to = task_update.assigned_to
    if task_update.actual_hours is not None:
        task.actual_hours = task_update.actual_hours
    if task_update.description:
        task.description = task_update.description

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    return {
        "success": True,
        "message": "Task status updated successfully",
        "task": TaskResponse.from_orm(task)
    }


@app.post("/api/v1/products/{product_id}/advance-stage")
def advance_product_stage(product_id: str, db: Session = Depends(get_db)):
    """
    Attempt to advance product to next stage gate
    Checks for blockers before allowing advancement
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check for stage gate blockers
    blockers = check_stage_gate_blockers(db, product)

    if blockers:
        return {
            "success": False,
            "message": "Cannot advance stage - blockers detected",
            "current_stage": product.current_stage.value,
            "current_gate": product.stage_gate.value,
            "blockers": blockers
        }

    # Advance stage
    stage_mapping = {
        "Stage 1": ("Architecture", "Stage 2"),
        "Stage 2": ("Development", "Stage 3"),
        "Stage 3": ("Integration", "Stage 4"),
        "Stage 4": ("Deployment", "Complete")
    }

    if product.stage_gate.value in stage_mapping:
        new_stage, new_gate = stage_mapping[product.stage_gate.value]
        product.current_stage = CurrentStage(new_stage)
        product.stage_gate = StageGate(new_gate)
        product.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(product)

        return {
            "success": True,
            "message": f"Product advanced to {new_stage} ({new_gate})",
            "previous_stage": product.current_stage.value,
            "new_stage": new_stage,
            "new_gate": new_gate
        }
    else:
        return {
            "success": False,
            "message": "Product is already at final stage",
            "current_stage": product.current_stage.value,
            "current_gate": product.stage_gate.value
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)