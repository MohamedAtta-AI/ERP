from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Site
from server.app.schemas.location import SiteCreate, SiteRead, SiteUpdate
from server.app.dependencies import require_admin, require_supervisor_or_admin

router = APIRouter()

@router.get("/", response_model=List[SiteRead])
async def list_locations(
    active_only: bool = True, # Ignored for now as Site model has no active field, keeping sig for compat
    session: Session = Depends(get_session),
    current_user=Depends(require_supervisor_or_admin),
):
    # If model had active field:
    # stmt = select(Site).where(Site.active == True) if active_only else select(Site)
    stmt = select(Site)
    return session.exec(stmt).all()

@router.post("/", response_model=SiteRead)
async def create_location(
    site_in: SiteCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    site = Site(**site_in.model_dump())
    session.add(site)
    session.commit()
    session.refresh(site)
    return site

@router.put("/{site_id}", response_model=SiteRead)
async def update_location(
    site_id: UUID,
    site_in: SiteUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    for k, v in site_in.model_dump(exclude_unset=True).items():
        setattr(site, k, v)
        
    session.add(site)
    session.commit()
    session.refresh(site)
    return site

@router.delete("/{site_id}")
async def delete_location(
    site_id: UUID,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    session.delete(site)
    session.commit()
    return {"ok": True}
