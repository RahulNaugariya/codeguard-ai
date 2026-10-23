import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_db
from src.models import ReviewRecord
from src.schemas import ReviewRequest, ReviewResponse, Issue
from src.reviewer import perform_ai_review

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "app": "CodeGuard AI",
        "status": "Running",
        "message": "Welcome to the CodeGuard AI API!",
    }


@router.post("/review", response_model=ReviewResponse)
async def review_code(request: ReviewRequest, db: Session = Depends(get_db)):
    code_to_review = request.code
    language_used = request.language

    # 1. Execute static review (raises 502 on Gemini failure)
    detected_issues = await perform_ai_review(
        code=code_to_review,
        language=language_used,
    )

    # Note: The string-based is_mock check has been entirely removed.

    # 2. Serialize and Persist with transaction safety
    issues_serialized = json.dumps([issue.model_dump() for issue in detected_issues])

    try:
        record = ReviewRecord(
            language=language_used,
            issues_json=issues_serialized,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failed while saving review record.",
        )

    return ReviewResponse(
        id=record.id,
        language=record.language,
        issues=detected_issues,
        created_at=record.created_at,
    )


@router.get("/reviews", response_model=List[ReviewResponse])
def list_reviews(db: Session = Depends(get_db)):
    try:
        records = db.query(ReviewRecord).order_by(ReviewRecord.created_at.desc()).all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed while fetching review history.",
        )

    response_list = []
    for record in records:
        try:
            raw_issues = json.loads(record.issues_json)
            parsed_issues = [Issue(**issue) for issue in raw_issues]
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Log the specific error internally to the server console
            print(f"CRITICAL: Data corruption in review ID {record.id}: {str(e)}")
            # Return a controlled, generic 500 error to the client
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data corruption detected in review ID {record.id}.",
            )

        response_list.append(
            ReviewResponse(
                id=record.id,
                language=record.language,
                issues=parsed_issues,
                created_at=record.created_at,
            )
        )

    return response_list


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review_by_id(review_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(ReviewRecord).filter(ReviewRecord.id == review_id).first()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed while fetching the review.",
        )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found.",
        )

    try:
        raw_issues = json.loads(record.issues_json)
        parsed_issues = [Issue(**issue) for issue in raw_issues]
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"CRITICAL: Data corruption in review ID {record.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data corruption detected in review ID {record.id}.",
        )

    return ReviewResponse(
        id=record.id,
        language=record.language,
        issues=parsed_issues,
        created_at=record.created_at,
    )
