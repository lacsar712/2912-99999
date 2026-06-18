"""
模型模块
"""
from .base import BaseModel
from .user import User
from .data import Data
from .category import Category
from .log import Log
from .config import Config as SystemConfig
from .production import (
    ProductionLine,
    Equipment,
    Sensor,
    ProductionTask,
    ProductionRecord,
    AlertRecord
)
from .safety import (
    HazardType,
    InspectionTask,
    HazardRecord,
    RectificationRecord,
    AccidentRecord
)
from .disposal import (
    DisposalOrder,
    DisposalApproval,
    DisposalResult
)
from .knowledge import (
    KnowledgeCategory,
    KnowledgeDocument,
    KnowledgeVersion,
    KnowledgeComment,
    KnowledgeLike
)
from .training import (
    TrainingCourse,
    TrainingPlan,
    TrainingAttendance,
    QualificationCertificate,
    PositionQualification
)
from .spare import SparePart, SpareInbound, SpareOutbound, SpareInventory
from .maintenance import MaintenanceWorkOrder
from .env_monitor import EnvArea, EnvMonitorPoint, EnvReading, EnvStandard
from .cost import CostElement, CostRecord, CostSummary
from .video_monitor import (
    Camera,
    CameraEquipmentRelation,
    PatrolGroup,
    PatrolGroupCamera,
    CaptureRecord
)
from .sop import (
    SOPDocument,
    SOPStep,
    SOPVersion,
    SOPTrainingRelation,
    SOPChecklist,
    SOPChecklistItem
)

__all__ = [
    'BaseModel',
    'User',
    'Data',
    'Category',
    'Log',
    'SystemConfig',
    'ProductionLine',
    'Equipment',
    'Sensor',
    'ProductionTask',
    'ProductionRecord',
    'AlertRecord',
    'HazardType',
    'InspectionTask',
    'HazardRecord',
    'RectificationRecord',
    'AccidentRecord',
    'DisposalOrder',
    'DisposalApproval',
    'DisposalResult',
    'KnowledgeCategory',
    'KnowledgeDocument',
    'KnowledgeVersion',
    'KnowledgeComment',
    'KnowledgeLike',
    'TrainingCourse',
    'TrainingPlan',
    'TrainingAttendance',
    'QualificationCertificate',
    'PositionQualification',
    'SparePart',
    'SpareInbound',
    'SpareOutbound',
    'SpareInventory',
    'MaintenanceWorkOrder',
    'EnvArea',
    'EnvMonitorPoint',
    'EnvReading',
    'EnvStandard',
    'CostElement',
    'CostRecord',
    'CostSummary',
    'Camera',
    'CameraEquipmentRelation',
    'PatrolGroup',
    'PatrolGroupCamera',
    'CaptureRecord',
    'SOPDocument',
    'SOPStep',
    'SOPVersion',
    'SOPTrainingRelation',
    'SOPChecklist',
    'SOPChecklistItem',
]
