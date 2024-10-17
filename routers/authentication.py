from utilities.auth import (
        get_hashed_password, 
        verify_password, 
        create_access_token, 
        get_current_user, 
        create_refresh_token, 
        oauth2_scheme
        )
from database.models import Users, TokenTable
from database.database import get_db
from schemas.schema import UserCreate

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_

from datetime import datetime

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(
                    Users.id
                    ).filter(or_(Users.username == user.username, Users.email == user.email)
                            ).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    hashed_password = get_hashed_password(user.password)
    new_user = Users(
                    username=user.username,
                    email=user.email,
                    role = user.role,
                    hashed_password=hashed_password
                   )
    db.add(new_user)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content="Registered successfully"
    )

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(Users).filter(Users.username==form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or Password is incorrect",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(
                           {"sub":db_user.username,"role":db_user.role.value}
                           )
    refresh_token = create_refresh_token(
                           {"sub":db_user.username,"role":db_user.role.value},
                           )
    token_db = TokenTable(
                    user_id=db_user.id,  
                    access_token=access_token,  
                    refresh_token=refresh_token
                    )
    db.add(token_db)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token":access_token,
            "refresh_token":refresh_token,
            "token_type":"Bearer"
        }
    )

@router.post("/logout")
def register_user(
            current_user: Users = Depends(get_current_user), 
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db)
            ):
    user_id = current_user.id
    token_record = db.query(TokenTable).all()
    info=[]
    for record in token_record :
        if (datetime.utcnow() - record.created_ts).days >1:
            info.append(record.user_id)
    if info:
        existing_token = db.query(TokenTable).where(TokenTable.user_id.in_(info)).delete()
        db.commit()
        
    existing_token = db.query(TokenTable).filter(TokenTable.user_id == user_id, TokenTable.access_token == token).first()
    if existing_token:
        existing_token.is_active=False
        db.add(existing_token)
        db.commit()
        db.refresh(existing_token)
    return {"message":"Logout Successfully"} 