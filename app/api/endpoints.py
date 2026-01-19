from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import uuid
import time
from app.models import DiagnosisResponse, ErrorResponse, Material, RepairStep, TimingInfo
from app.services.image_processor import ImageProcessor, ImageQualityError
from app.services.vision_service import vision_service, VisionServiceError
from app.services.session_manager import session_manager
from app.services.cache_manager import cache_manager
from app.utils.material_normalizer import MaterialNormalizer

router = APIRouter()


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(
    image: UploadFile = File(..., description="Image of broken item"),
    session_id: Optional[str] = Form(None, description="Session ID for follow-up questions"),
    question: Optional[str] = Form(None, description="Follow-up question"),
    model: Optional[str] = Form(None, description="OpenAI model to use (gpt-4o, gpt-4o-mini)")
):
    """
    Diagnose a broken household item from an image.

    For initial diagnosis: Upload image only.
    For follow-up questions: Include session_id and question.
    """
    start_time = time.time()
    timing = {
        'image_processing_time': 0.0,
        'cache_lookup_time': 0.0,
        'openai_api_time': 0.0,
        'normalization_time': 0.0,
        'cache_source': 'miss'
    }

    try:
        # Read image bytes
        image_bytes = await image.read()
        filename = image.filename or ""

        # Step 1: Process image (validate, check quality, preprocess, hash)
        img_start = time.time()
        try:
            processed_bytes, sha256_hash, phash = ImageProcessor.process_upload(
                image_bytes, filename
            )
            timing['image_processing_time'] = time.time() - img_start
        except ImageQualityError as e:
            timing['image_processing_time'] = time.time() - img_start
            # Return "image unclear" response
            return DiagnosisResponse(
                diagnosis="Image unclear",
                confidence=0.1,
                materials=[],
                tools_required=[],
                repair_steps=[],
                warnings=[str(e), "Please retake the photo with better lighting and focus."],
                followup_questions=[],
                timing=TimingInfo(
                    total_time=time.time() - start_time,
                    image_processing_time=timing['image_processing_time'],
                    cache_source='rejected'
                )
            )

        # Handle follow-up question
        if question and session_id:
            return await _handle_followup(session_id, question, start_time)

        # Step 2: Check exact cache
        cache_start = time.time()
        cached = cache_manager.get_exact(sha256_hash, question or "")
        timing['cache_lookup_time'] = time.time() - cache_start

        if cached:
            timing['cache_source'] = 'exact'
            return _format_diagnosis_response(
                cached, session_id, timing, time.time() - start_time
            )

        # Step 3: Check perceptual cache (similar images)
        perc_start = time.time()
        cached = cache_manager.get_perceptual(phash)
        timing['cache_lookup_time'] += time.time() - perc_start

        if cached:
            timing['cache_source'] = 'perceptual'
            return _format_diagnosis_response(
                cached, session_id, timing, time.time() - start_time
            )

        # Step 4: Call GPT-4o Vision
        cache_manager.record_miss()
        timing['cache_source'] = 'miss'

        openai_start = time.time()
        try:
            diagnosis = await vision_service.diagnose_image(processed_bytes, model=model)
            timing['openai_api_time'] = time.time() - openai_start
        except VisionServiceError as e:
            raise HTTPException(status_code=500, detail=f"Vision service error: {str(e)}")

        # Step 5: Normalize materials (remove brands/SKUs/URLs)
        norm_start = time.time()
        if 'materials' in diagnosis:
            diagnosis['materials'] = MaterialNormalizer.normalize_materials(diagnosis['materials'])
        timing['normalization_time'] = time.time() - norm_start

        # Step 6: Cache the result
        new_session_id = session_id or session_manager.create_session()
        cache_manager.set(sha256_hash, phash, diagnosis, question or "")
        session_manager.update_session(new_session_id, sha256_hash, diagnosis)

        # Step 7: Format and return response
        return _format_diagnosis_response(
            diagnosis, new_session_id, timing, time.time() - start_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


async def _handle_followup(session_id: str, question: str, start_time: float) -> DiagnosisResponse:
    """Handle follow-up question with session context."""
    timing = {
        'image_processing_time': 0.0,
        'cache_lookup_time': 0.0,
        'openai_api_time': 0.0,
        'normalization_time': 0.0,
        'cache_source': 'followup'
    }

    # Get session context
    context = session_manager.get_context(session_id)
    if not context:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please start a new diagnosis."
        )

    # Get previous diagnosis
    previous_diagnosis = session_manager.get_latest_diagnosis(session_id)

    # Call GPT for follow-up
    openai_start = time.time()
    try:
        followup_response = await vision_service.handle_followup(
            question, context, previous_diagnosis
        )
        timing['openai_api_time'] = time.time() - openai_start
    except VisionServiceError as e:
        raise HTTPException(status_code=500, detail=f"Vision service error: {str(e)}")

    # Normalize any additional materials
    norm_start = time.time()
    if 'additional_materials' in followup_response:
        followup_response['additional_materials'] = MaterialNormalizer.normalize_materials(
            followup_response['additional_materials']
        )
    timing['normalization_time'] = time.time() - norm_start

    # Merge follow-up response with previous diagnosis
    merged_diagnosis = _merge_followup_response(previous_diagnosis, followup_response)

    # Update session
    session_manager.update_session(session_id, "followup", merged_diagnosis)

    return _format_diagnosis_response(
        merged_diagnosis, session_id, timing, time.time() - start_time
    )


def _merge_followup_response(previous: dict, followup: dict) -> dict:
    """Merge follow-up response into previous diagnosis."""
    merged = previous.copy()

    # Add additional materials
    if 'additional_materials' in followup:
        existing_materials = merged.get('materials', [])
        merged['materials'] = existing_materials + followup['additional_materials']

    # Add additional steps
    if 'additional_steps' in followup:
        existing_steps = merged.get('repair_steps', [])
        # Renumber additional steps
        start_step = len(existing_steps) + 1
        for i, step in enumerate(followup['additional_steps']):
            step['step'] = start_step + i
        merged['repair_steps'] = existing_steps + followup['additional_steps']

    # Add additional warnings
    if 'additional_warnings' in followup:
        existing_warnings = merged.get('warnings', [])
        merged['warnings'] = existing_warnings + followup['additional_warnings']

    return merged


def _format_diagnosis_response(
    diagnosis: dict,
    session_id: str = None,
    timing: dict = None,
    total_time: float = None
) -> DiagnosisResponse:
    """Format diagnosis dictionary into DiagnosisResponse model."""
    # Build timing info if provided
    timing_info = None
    if timing and total_time is not None:
        timing_info = TimingInfo(
            total_time=round(total_time, 3),
            image_processing_time=round(timing.get('image_processing_time', 0.0), 3),
            cache_lookup_time=round(timing.get('cache_lookup_time', 0.0), 3),
            openai_api_time=round(timing.get('openai_api_time', 0.0), 3),
            normalization_time=round(timing.get('normalization_time', 0.0), 3),
            cache_source=timing.get('cache_source')
        )

    # Handle "unclear" status
    if diagnosis.get('status') == 'unclear':
        return DiagnosisResponse(
            diagnosis=diagnosis.get('reason', 'Image unclear'),
            confidence=0.1,
            professional_help_recommended=None,
            professional_help_reason=None,
            estimated_time=None,
            difficulty=None,
            materials=[],
            tools_required=[],
            repair_steps=[],
            warnings=diagnosis.get('suggestions', ['Please retake the photo with better lighting and focus.']),
            followup_questions=[],
            session_id=session_id,
            timing=timing_info
        )

    # Parse materials
    materials = []
    for mat in diagnosis.get('materials', []):
        materials.append(Material(
            name=mat.get('name', ''),
            category=mat.get('category', 'other'),
            search_query=mat.get('search_query', mat.get('name', ''))
        ))

    # Parse repair steps
    repair_steps = []
    for step in diagnosis.get('repair_steps', []):
        repair_steps.append(RepairStep(
            step=step.get('step', 0),
            title=step.get('title', ''),
            instruction=step.get('instruction', ''),
            safety_tip=step.get('safety_tip')
        ))

    # Build response
    return DiagnosisResponse(
        diagnosis=diagnosis.get('failure_mode', diagnosis.get('diagnosis', 'Unknown issue')),
        confidence=float(diagnosis.get('confidence', 0.5)),
        issue_type=diagnosis.get('issue_type'),
        professional_help_recommended=diagnosis.get('professional_help_recommended'),
        professional_help_reason=diagnosis.get('professional_help_reason'),
        estimated_time=diagnosis.get('estimated_time'),
        difficulty=diagnosis.get('difficulty'),
        materials=materials,
        tools_required=diagnosis.get('tools_required', diagnosis.get('tools', [])),
        repair_steps=repair_steps,
        warnings=diagnosis.get('safety_warnings', diagnosis.get('warnings', [])),
        followup_questions=diagnosis.get('followup_questions', []),
        session_id=session_id,
        timing=timing_info
    )


@router.get("/health")
async def health():
    """Health check endpoint."""
    cache_stats = cache_manager.get_stats()
    session_count = session_manager.get_session_count()

    return {
        "status": "healthy",
        "cache_stats": cache_stats,
        "active_sessions": session_count
    }


@router.post("/cache/clear")
async def clear_cache():
    """Clear all caches (admin endpoint)."""
    cache_manager.clear_all()
    return {"status": "cache cleared"}
