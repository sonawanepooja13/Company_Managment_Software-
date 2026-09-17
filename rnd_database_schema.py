"""
R&D Database Schema - SQLAlchemy Models
Complete relational schema for 8 interlinked R&D modules with proper foreign key relationships
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


# Enum definitions
class StageGate(enum.Enum):
    STAGE_1 = "Stage 1"  # Requirements & Feasibility
    STAGE_2 = "Stage 2"  # Architectural Design
    STAGE_3 = "Stage 3"  # Integration & Testing
    STAGE_4 = "Stage 4"  # Compliance, Pilot Production & Deployment
    COMPLETE = "Complete"


class CurrentStage(enum.Enum):
    REQUIREMENTS = "Requirements"
    ARCHITECTURE = "Architecture"
    DEVELOPMENT = "Development"
    INTEGRATION = "Integration"
    COMPLIANCE = "Compliance"
    DEPLOYMENT = "Deployment"


class TaskStatus(enum.Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    CODE_REVIEW = "Code Review"
    HARDWARE_TESTING = "Hardware Testing"
    DONE = "Done"


class HardwareStatus(enum.Enum):
    DESIGN = "Design"
    PROTOTYPE = "Prototype"
    TESTING = "Testing"
    PRODUCTION = "Production"
    RETIRED = "Retired"


class RiskLevel(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskStatus(enum.Enum):
    IDENTIFIED = "Identified"
    MITIGATING = "Mitigating"
    RESOLVED = "Resolved"
    ACCEPTED = "Accepted"


class ComplianceStatus(enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    PASSED = "Passed"
    FAILED = "Failed"
    EXEMPTED = "Exempted"


class ComponentStatus(enum.Enum):
    AVAILABLE = "Available"
    LOW_STOCK = "Low Stock"
    OUT_OF_STOCK = "Out of Stock"
    DISCONTINUED = "Discontinued"


# 1. Product Development (PDLC) - Core Module
class Product(Base):
    """Core product lifecycle management - Product-centric core of the system"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., PDLC-2026082422
    product_name = Column(String(200), nullable=False)
    product_type = Column(String(50), nullable=False)  # Embedded System, IoT Device, Firmware, Hardware, Software
    current_stage = Column(Enum(CurrentStage), default=CurrentStage.REQUIREMENTS)
    stage_gate = Column(Enum(StageGate), default=StageGate.STAGE_1)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    team_lead = Column(String(100))
    completion_percentage = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="product", cascade="all, delete-orphan")
    sprints = relationship("Sprint", back_populates="product", cascade="all, delete-orphan")
    hardware_prototypes = relationship("HardwarePrototype", back_populates="product", cascade="all, delete-orphan")
    components = relationship("ProductComponent", back_populates="product", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="product", cascade="all, delete-orphan")
    compliance_records = relationship("ComplianceRecord", back_populates="product", cascade="all, delete-orphan")


# 2. Projects & Tasks Module
class Task(Base):
    """Breaks down products into actionable tasks with hardware dependencies"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., TASK-2026082422-001
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False, index=True)
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50), nullable=False)  # Firmware, Hardware, Integration, Testing, Documentation, Bug Fix
    status = Column(Enum(TaskStatus), default=TaskStatus.TO_DO)
    assigned_to = Column(String(100))
    hardware_dependent = Column(Boolean, default=False)
    required_hardware_id = Column(String(50), ForeignKey('hardware_prototypes.hardware_id'))
    required_component_id = Column(String(50), ForeignKey('components.component_id'))
    due_date = Column(Date)
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0)
    priority = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    description = Column(Text)
    sprint_id = Column(String(50), ForeignKey('sprints.sprint_id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="tasks")
    required_hardware = relationship("HardwarePrototype", foreign_keys=[required_hardware_id])
    required_component = relationship("Component", foreign_keys=[required_component_id])
    sprint = relationship("Sprint", back_populates="tasks")


# 3. Sprint Management Module
class Sprint(Base):
    """Groups tasks into sprints for agile engineering tracking"""
    __tablename__ = 'sprints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sprint_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., SPRINT-20260824-W1
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False, index=True)
    sprint_name = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="Planned")  # Planned, Active, Completed, Cancelled
    velocity = Column(Float, default=0)  # Story points completed
    goal = Column(Text)
    retrospective = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")


# 4. Hardware & Prototypes Module
class HardwarePrototype(Base):
    """Tracks physical hardware builds, revisions, and testing statuses"""
    __tablename__ = 'hardware_prototypes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hardware_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., HW-2026082422-REV1
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False, index=True)
    hardware_name = Column(String(200), nullable=False)
    hardware_type = Column(String(50), nullable=False)  # PCB, Evaluation Board, Prototype, Production Unit
    status = Column(Enum(HardwareStatus), default=HardwareStatus.DESIGN)
    pcb_status = Column(String(20), default="Not Started")  # Not Started, In Design, Fabrication, Assembly, Complete
    bringup_status = Column(String(20), default="Not Started")  # Not Started, In Progress, Complete, Failed
    revision = Column(String(20), default="REV1")
    quantity = Column(Integer, default=1)
    location = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="hardware_prototypes")


# 5. Components & Supply Module (Links to Warehouse)
class Component(Base):
    """Warehouse electronic components with stock tracking"""
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., COMP-RES-10K-001
    item_id = Column(String(50), ForeignKey('warehouse_items.item_id'))  # Link to warehouse
    component_name = Column(String(200), nullable=False)
    part_number = Column(String(100))
    manufacturer = Column(String(100))
    category = Column(String(50))
    specifications = Column(Text)  # Voltage, Current, Package, etc.
    current_stock = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=10)
    max_stock_level = Column(Integer, default=100)
    unit_of_measurement = Column(String(20), default="Pcs")
    status = Column(Enum(ComponentStatus), default=ComponentStatus.AVAILABLE)
    supplier = Column(String(100))
    lead_time_days = Column(Integer, default=7)
    unit_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    used_in_products = relationship("ProductComponent", back_populates="component")


class ProductComponent(Base):
    """Many-to-many relationship between Products and Components (BOM)"""
    __tablename__ = 'product_components'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False, index=True)
    component_id = Column(String(50), ForeignKey('components.component_id'), nullable=False, index=True)
    quantity_required = Column(Integer, default=1)
    quantity_allocated = Column(Integer, default=0)
    is_critical = Column(Boolean, default=False)  # Critical for production
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="components")
    component = relationship("Component", back_populates="used_in_products")

    # Unique constraint to prevent duplicate product-component pairs
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


# 6. Risk Management Module
class Risk(Base):
    """Identifies engineering, component-shortage, or compliance risks"""
    __tablename__ = 'risks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., RISK-2026082422-001
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False, index=True)
    task_id = Column(String(50), ForeignKey('tasks.task_id'))
    risk_name = Column(String(200), nullable=False)
    risk_type = Column(String(50), nullable=False)  # Engineering, Component Shortage, Compliance, Schedule, Resource
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    status = Column(Enum(RiskStatus), default=RiskStatus.IDENTIFIED)
    probability = Column(Integer, default=50)  # 1-100%
    impact = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    description = Column(Text)
    mitigation_plan = Column(Text)
    owner = Column(String(100))
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="risks")


# 7. Team & Resources Module
class TeamMember(Base):
    """Manages engineering resources and team leads"""
    __tablename__ = 'team_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., TEAM-DEV-001
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # Embedded Engineer, Hardware Engineer, Project Manager, QA Engineer
    specialization = Column(String(100))  # Firmware, PCB Design, Testing, etc.
    email = Column(String(100))
    phone = Column(String(20))
    workload_capacity = Column(Integer, default=40)  # Hours per week
    current_workload = Column(Integer, default=0)
    skills = Column(Text)  # Comma-separated skills
    availability = Column(String(20), default="Available")  # Available, Partially Available, Unavailable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TeamAllocation(Base):
    """Tracks team member allocation to products and tasks"""
    __tablename__ = 'team_allocations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    allocation_id = Column(String(50), unique=True, nullable=False, index=True)
    member_id = Column(String(50), ForeignKey('team_members.member_id'), nullable=False)
    product_id = Column(String(50), ForeignKey('products.product_id'))
    task_id = Column(String(50), ForeignKey('tasks.task_id'))
    role_in_project = Column(String(50))  # Lead, Member, Reviewer
    allocation_percentage = Column(Integer, default=100)  # % of time allocated
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)


# 8. Compliance & Certification Module
class ComplianceRecord(Base):
    """Tracks regulatory standards required before product deployment"""
    __tablename__ = 'compliance_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    certification_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., CERT-CE-2026082422
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False, index=True)
    certification_type = Column(String(50), nullable=False)  # CE, FCC, UL, ISO, IP Rating, etc.
    certification_name = Column(String(200), nullable=False)
    standard_version = Column(String(50))  # e.g., CE 2014/30/EU, FCC Part 15
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING)
    test_date = Column(Date)
    expiry_date = Column(Date)
    test_lab = Column(String(100))
    certificate_number = Column(String(100))
    required_for_stage = Column(String(20), default="Stage 4")  # Stage gate where this is required
    is_blocking = Column(Boolean, default=True)  # Blocks stage gate if not passed
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="compliance_records")


# Database connection setup
def get_database_url():
    """Returns database URL - can be configured for different databases"""
    return "sqlite:///rnd_database.db"  # Default to SQLite for development
    # For PostgreSQL: return "postgresql://user:password@localhost/rnd_database"
    # For MySQL: return "mysql://user:password@localhost/rnd_database"


def create_engine_and_session():
    """Create database engine and session"""
    engine = create_engine(get_database_url(), echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session()


# Database initialization
def init_database():
    """Initialize database with all tables"""
    engine, Session = create_engine_and_session()
    print("Database initialized successfully!")
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    return engine, Session


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()