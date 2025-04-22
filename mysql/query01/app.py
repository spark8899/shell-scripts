from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
import logging.config
import os

# 加载日志配置
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("app")

# 配置类
class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    APP_SECRET_KEY: str
    APP_USERNAME: str
    APP_PASSWORD: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# 创建FastAPI应用
app = FastAPI()

# 设置静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# MySQL数据库连接
DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(DATABASE_URL, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    if username != settings.APP_USERNAME:
        return False
    if not verify_password(password, get_password_hash(settings.APP_PASSWORD)):
        return False
    return True

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if username != settings.APP_USERNAME:
        raise credentials_exception

    return username

# 登录页面
@app.get("/login")
async def login_page(request: Request):
    logger.info("访问登录页面")
    return templates.TemplateResponse("login.html", {"request": request})

# 处理登录
@app.post("/login")
async def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):
    logger.info(f"尝试登录，用户名: {username}")

    if not authenticate_user(username, password):
        logger.warning(f"登录失败，用户名: {username}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    logger.info(f"用户 {username} 登录成功")

    response = templates.TemplateResponse(
        "query01.html",
        {"request": request, "username": username}
    )
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

# 查询页面
@app.get("/query")
async def query_page(request: Request, username: str = Depends(get_current_user)):
    logger.info(f"用户 {username} 访问查询页面")
    return templates.TemplateResponse(
        "query01.html",
        {"request": request, "username": username}
    )

# 处理查询
@app.post("/query")
async def handle_query(
    request: Request,
    show_ids: str = Form(...),
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"用户 {username} 执行查询: {show_ids}")

    try:
        # 转换输入为列表
        #ids_list = [id.strip() for id in show_ids.split(",") if id.strip()]
        ids_list = []
        for line in show_ids.splitlines():
            # 移除行首尾空白，然后按逗号分割
            cleaned_line = line.strip()
            if cleaned_line:  # 忽略空行
                ids_list.extend([id.strip() for id in cleaned_line.split(",") if id.strip()])

        if not ids_list:
            raise ValueError("请输入至少一个有效的show_id")


        # 执行SQL查询 - MySQL版本
        sql = text("""
            SELECT a.show_id, b.photo_id
            FROM user a
            JOIN user_photo b ON a.id = b.uid
            WHERE FIND_IN_SET(a.show_id, :show_ids_csv) order by a.show_id
        """)

        #with engine.connect() as connection:
        #    result = connection.execute(sql, {"show_ids_csv": ",".join(ids_list)})
        #    rows = result.fetchall()
        result = db.execute(sql, {"show_ids_csv": ",".join(ids_list)})
        rows = result.fetchall()

        logger.info(f"用户 {username} 查询成功，结果数量: {len(rows)}")

        return templates.TemplateResponse(
            "query01.html",
            {
                "request": request,
                "results": rows,
                "show_ids": show_ids,
                "username": username
            }
        )
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        raise e

    except Exception as e:
        logger.error(f"用户 {username} 查询出错: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "query01.html",
            {
                "request": request,
                "error": str(e),
                "show_ids": show_ids,
                "username": username
            }
        )

# 登出
@app.get("/logout")
async def logout(username: str = Depends(get_current_user)):
    logger.info(f"用户 {username} 退出登录")
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

if __name__ == "__main__":
    import uvicorn
    logger.info("启动FastAPI应用")
    uvicorn.run(app, host="0.0.0.0", port=8000)
