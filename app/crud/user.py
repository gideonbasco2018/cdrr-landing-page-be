from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_google_id(db: Session, google_id: str) -> User | None:
    return db.query(User).filter(User.google_id == google_id).first()


def create_user(db: Session, *, email: str, name: str, google_id: str, avatar_url: str | None) -> User:
    user = User(email=email, name=name, google_id=google_id, avatar_url=avatar_url)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(db: Session, user: User, *, name: str, avatar_url: str | None) -> User:
    user.name = name
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user


def get_or_create_from_google(db: Session, *, google_id: str, email: str, name: str, avatar_url: str | None) -> User:
    user = get_user_by_google_id(db, google_id)
    if user:
        return update_user_profile(db, user, name=name, avatar_url=avatar_url)

    existing_by_email = get_user_by_email(db, email)
    if existing_by_email:
        existing_by_email.google_id = google_id
        return update_user_profile(db, existing_by_email, name=name, avatar_url=avatar_url)

    return create_user(db, email=email, name=name, google_id=google_id, avatar_url=avatar_url)
