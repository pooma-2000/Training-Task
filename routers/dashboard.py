from utilities.auth import RoleChecker, get_current_user
from routers.authentication import router
from database.models import Users

from fastapi import Depends, status
from fastapi.responses import JSONResponse

@router.get("/users/me")
async def read_users_me(current_user: Users = Depends(get_current_user)):
    try:
        return current_user
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={e}
        )
    
@router.get("/admin")
def admin_panel(permission: bool = Depends(RoleChecker(required_permissions=['admin']))):
     if permission:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content="This is admin panel"
        )