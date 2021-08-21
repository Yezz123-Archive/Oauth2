from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import JWTError, jwt
import pyotp
from sqlalchemy.orm import Session
from security.security import pwd_context
from core import crud
from model import schemas
from database import database
from decouple import config

router = APIRouter(
    tags=["Oauth2"],
    prefix="/Oauth2"
)

get_db = database.get_db


SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/Oauth2/token")


# Verify the Hashed Password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Get The Hashed Password


def get_password_hash(password):
    return pwd_context.hash(password)

# Get The Current User by Username


def get_user(db: Session, username: str):
    return crud.get_user_by_username(db, username)

# Authenticate the Users using Pyotp


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password[:-6], user.hashed_password):
        return False
    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(password[-6:]):
        return False
    return user

# Create the Access Token and Encoded with JWT


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Get The Current Login User


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Get The Most Active User


def get_current_active_user(
        current_user: schemas.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Get the Most Active Admin


def get_current_active_admin_user(
        current_user: schemas.User = Depends(get_current_active_user), ):
    if current_user.role != schemas.Role.admin:
        raise HTTPException(status_code=400,
                            detail="User has insufficient permissions")
    return current_user


@router.post("/token", response_model=schemas.Token)
def access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                 db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username},
                                       expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/", response_model=schemas.User)
def Create_New_User(
        user: schemas.UserCreate,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_active_admin_user)):
    return crud.create_user(db, user)


@router.get("/users/me/", response_model=schemas.User)
async def Current_User(
        current_user: schemas.User = Depends(get_current_active_user)):
    return current_user


@router.get("/users/{user_id}", response_model=schemas.User)
def Get_User_By_ID(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_active_admin_user)):
    return crud.get_user(db, user_id)


@router.put("/users/me/", response_model=schemas.User)
def Update_Record(user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    return crud.update_user_self(db, current_user, user_update)
