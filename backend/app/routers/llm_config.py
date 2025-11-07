from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..llm_service import LLMService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.LLMConfig)
async def create_or_update_llm_config(
    config: schemas.LLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    logger.info(f"Received config: purpose={config.purpose}, api_url={config.api_url}")
    
    existing = db.query(models.LLMConfig).filter(
        models.LLMConfig.purpose == config.purpose
    ).first()
    
    if existing:
        logger.info(f"Updating existing config ID: {existing.id}")
        
        # Determine which fields are critical and require retesting
        critical_fields = []
        if config.provider_type == models.LLMProviderType.AZURE:
            critical_fields = ['azure_endpoint', 'azure_api_key', 'azure_deployment_name', 'azure_api_version']
        elif config.provider_type == models.LLMProviderType.BEDROCK:
            critical_fields = ['aws_region', 'aws_access_key_id', 'aws_secret_access_key', 'aws_model_id']
        elif config.provider_type == models.LLMProviderType.LOCAL:
            critical_fields = ['api_url', 'api_key', 'model_name']
        
        # Check if any critical fields changed
        critical_field_changed = False
        for key, value in config.dict().items():
            if key in critical_fields and value is not None:
                old_value = getattr(existing, key, None)
                if old_value != value:
                    critical_field_changed = True
                    break
        
        # Update all fields
        for key, value in config.dict().items():
            setattr(existing, key, value)
        
        # Only reset status to "Not Tested" if critical fields changed
        # This way, if user just changes non-critical fields (like reasoning_effort), 
        # the status stays as "Success" if it was already tested
        # NOTE: We do NOT auto-test here - user must explicitly click "Test" button
        if critical_field_changed:
            existing.status = "Not Tested"
            logger.info(f"Critical fields changed, resetting status to 'Not Tested' (user must test manually)")
        else:
            logger.info(f"No critical fields changed, preserving status: {existing.status}")
        
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated config: id={existing.id}, status={existing.status}")
        return existing
    else:
        logger.info("Creating new config")
        # Ensure new configs always start with "Not Tested" status
        config_dict = config.dict()
        config_dict['status'] = "Not Tested"  # Explicitly set status, overriding any from schema
        db_config = models.LLMConfig(**config_dict)
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        logger.info(f"Created config: id={db_config.id}, status={db_config.status}")
        return db_config

@router.get("/", response_model=List[schemas.LLMConfig])
def list_llm_configs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    configs = db.query(models.LLMConfig).all()
    return configs

@router.post("/{config_id}/test")
async def test_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    logger.info(f"========== TEST ENDPOINT CALLED: config_id={config_id} ==========")
    
    config = db.query(models.LLMConfig).filter(
        models.LLMConfig.id == config_id
    ).first()
    if not config:
        logger.error(f"Config not found: {config_id}")
        raise HTTPException(status_code=404, detail="LLM config not found")
    
    logger.info(f"Config found: id={config.id}, purpose={config.purpose}")
    logger.info(f"Provider Type: {config.provider_type}")
    logger.info(f"Model Name from DB: '{config.model_name}'")

    result = await LLMService.test_llm_connection(config)
    logger.info(f"Test result: {result}")
    
    config.status = result["status"]
    db.commit()
    
    return result