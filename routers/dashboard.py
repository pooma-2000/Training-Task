from utilities.auth import RoleChecker, get_current_user
from routers.authentication import router
from database.models import Users
from database.database import get_db, engine
from database.db_enum import Roles, Status
from schemas.schema import UserDetails

from fastapi import Depends, status, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from typing import Optional

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/users/me", description="To check the current user")
async def read_users_me(current_user: Users = Depends(get_current_user)):
        try:
            return current_user
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={e}
            )

@router.get("/admin", description="Restricting this route for roles other than admin")
def admin_panel(permission: bool = Depends(RoleChecker(required_permissions=['admin']))):
        if permission:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content="This is admin panel"
            )
     
@router.get("/user_profile", description="To view the user's profile details")
def get_user_profile(
        user: Users = Depends(get_current_user),
        db: Session = Depends(get_db),
        ):
        user_data = db.query(Users).filter(Users.id == user.id).first()
        return user_data if user_data else "User not found"

@router.put("/edit_user", description="To edit the user's profile")
def edit_user_details(
        user_details: UserDetails, 
        user: Users = Depends(get_current_user),
        db: Session = Depends(get_db),
        ):
        user_id = user_details.user_id
        user_data = db.query(Users).filter(Users.id == user_id).first()
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user_data.username = user_details.username
        user_data.email = user_details.email
        user_data.role = user_details.role
        db.commit()
        return "User details updated successfully"

@router.delete("/delete_user")
def delete_user(
        user_id: int,
        user: Users = Depends(get_current_user),
        db: Session = Depends(get_db),
        ):
        user_data = db.query(Users).filter(Users.id == user_id).first()
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user_data.is_active = False
        db.commit()
        return "User deleted successfully"  
    
@router.get("/manage_users", response_model=Page[UserDetails])
def manage_all_users(
        size: int,
        page: int,
        status: Status,
        db: Session = Depends(get_db),
        user: Users = Depends(get_current_user)
        ):
        params = Params(size=size, page=page)
        if status.value == "active":
            users = db.query(
                Users.id,
                Users.username,
                Users.email,
                Users.role
                ).filter(
                        Users.is_active == True)
        elif status.value == "inactive":
            users = db.query(
                Users.id,
                Users.username,
                Users.email,
                Users.role
                ).filter(
                        Users.is_active == False)
     
        return paginate(users,
                        params=params,
                        )

@router.get("/search_user", description="To search for specific user based on username or roles")
def search_user(
        username: Optional[str] | None = None,
        role: Optional[Roles] | None = None,
        db: Session = Depends(get_db),
        user: Users = Depends(get_current_user)
        ):
      
        if username:
                user_data = db.query(Users).filter(Users.username == username, Users.is_active == True).first()
        elif role:
                user_data = db.query(Users).filter(Users.role == role, Users.is_active == True).all()
        else:
               raise HTTPException(
                      status_code=status.HTTP_400_BAD_REQUEST,
                      detail="Provide the username or role to search for users"
               )
        if not user_data:
               raise HTTPException(
                      status_code=status.HTTP_404_NOT_FOUND,
                      detail="User not found"
               )
        users_list = [
            {
                "user id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.role
            }for user in user_data
            ]
        return users_list

      


    

   # users_list = [
        #     {
        #         "user id": user.id,
        #         "username": user.username,
        #         "email": user.email,
        #         "roles": user.role
        #     }for user in users
        #     ]