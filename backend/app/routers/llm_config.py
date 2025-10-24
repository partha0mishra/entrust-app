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
        for key, value in config.dict().items():
            setattr(existing, key, value)
        existing.status = "Not Tested"
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated config: id={existing.id}, api_url={existing.api_url}")
        return existing
    else:
        logger.info("Creating new config")
        db_config = models.LLMConfig(**config.dict())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        logger.info(f"Created config: id={db_config.id}, api_url={db_config.api_url}")
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
    logger.info(f"API URL from DB: '{config.api_url}'")
    logger.info(f"Model Name from DB: '{config.model_name}'")
    logger.info(f"API Key from DB: {'SET' if config.api_key else 'NOT SET'}")
    
    result = await LLMService.test_llm_connection(
        config.api_url, 
        config.api_key,
        config.model_name  # PASS MODEL NAME
    )
    logger.info(f"Test result: {result}")
    
    config.status = result["status"]
    db.commit()
    
    return result