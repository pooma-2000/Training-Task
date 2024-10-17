from utilities.auth import RoleChecker, get_current_user
from routers.authentication import router
from database.models import Users
from database.database import get_db
from database.db_enum import Roles
from schemas.schema import UserDetails

from fastapi import Depends, status, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
    
@router.get("/manage_users", description="To view all the user's details")
def manage_all_users(
                db: Session = Depends(get_db),
                user: Users = Depends(get_current_user)
                ):
        users = db.query(Users).filter(Users.is_active == True).all()
        users_list = [
            {
                "user id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.role
            }for user in users
            ]
        return users_list


    

