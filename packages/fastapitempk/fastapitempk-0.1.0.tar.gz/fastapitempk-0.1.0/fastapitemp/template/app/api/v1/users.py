from fastapi import APIRouter 

user_router = APIRouter()

@user_router.get('/me')
async def get_me():
	return {"message": "User router"}