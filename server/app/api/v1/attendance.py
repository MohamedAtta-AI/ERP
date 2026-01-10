import cv2
import numpy as np
from fastapi import APIRouter

from server.db import get_session
from server.app.services import FaceRecognitionService
from server.config import config

router = APIRouter()
recognizer = FaceRecognitionService()


@router.post("/check-in", response_model=AttendanceCheckInResponse)
async def check_in(
    request: AttendanceCheckInRequest,
    session: AsyncSession = Depends(get_session),
):