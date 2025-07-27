"""
Модели данных для проекта Vetbot
"""

from vetbot_improved.models.user import User
from vetbot_improved.models.doctor import Doctor
from vetbot_improved.models.consultation import (
    Consultation,
    ActiveConsultation,
    ConsultationMessage,
    DoctorNotification
)
from vetbot_improved.models.vet_call import VetCall
from vetbot_improved.models.admin import AdminSession, AdminMessage, AdminMessageQueue

__all__ = [
    "User",
    "Doctor",
    "Consultation",
    "ActiveConsultation",
    "ConsultationMessage",
    "DoctorNotification",
    "VetCall",
    "AdminSession",
    "AdminMessage",
    "AdminMessageQueue"
]