from fastapi import FastAPI, Depends
from api.security import verify_bot_secret
from api.routers import auth, users, invite_codes, agreements, admin, groups, students, schedules, lessons

app = FastAPI(title="AleksSchool Bot API", version="1.0.0")

# All routers protected by X-Bot-Secret
for router in [
    auth.router, users.router, invite_codes.router,
    agreements.router, admin.router, groups.router,
    students.router, schedules.router, lessons.router,
]:
    app.include_router(router, dependencies=[Depends(verify_bot_secret)])

@app.get("/health")
async def health():
    return {"status": "ok"}
