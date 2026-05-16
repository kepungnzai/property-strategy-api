from typing import Optional
from datetime import datetime
from bson import ObjectId
from graphql_microservice.database.connection import get_database
from graphql_microservice.database.models import GoogleUser
#from graphql_microservice.database.models import UserCreate, UserUpdate


# async def create_user(user_data: UserCreate) -> User:
#     db = await get_database()
#     now = datetime.utcnow()
#     document = {
#         "googleId": user_data.google_id,
#         "email": user_data.email,
#         "name": user_data.name,
#         "picture": user_data.picture,
#         "createdAt": now,
#         "updatedAt": now,
#     }
#     result = await db.users.insert_one(document)
#     document["id"] = str(result.inserted_id)
#     return User(**document)


async def find_user_by_google_id(google_id: str) -> Optional[GoogleUser]:
    db = await get_database()
    document = await db.users.find_one({"googleId": google_id})
    if document:
        document["id"] = str(document.pop("_id"))
        return GoogleUser(**document)
    return None


# async def find_user_by_id(user_id: str) -> Optional[User]:
#     if not ObjectId.is_valid(user_id):
#         return None
#     db = await get_database()
#     document = await db.users.find_one({"_id": ObjectId(user_id)})
#     if document:
#         document["id"] = str(document.pop("_id"))
#         return User(**document)
#     return None


# async def find_user_by_email(email: str) -> Optional[User]:
#     db = await get_database()
#     document = await db.users.find_one({"email": email})
#     if document:
#         document["id"] = str(document.pop("_id"))
#         return User(**document)
#     return None


# async def update_user(user_id: str, update_data: UserUpdate) -> Optional[User]:
#     if not ObjectId.is_valid(user_id):
#         return None

#     db = await get_database()
#     update_dict = update_data.model_dump(exclude_unset=True)
#     if not update_dict:
#         return await find_user_by_id(user_id)

#     update_dict["updatedAt"] = datetime.utcnow()
#     result = await db.users.find_one_and_update(
#         {"_id": ObjectId(user_id)},
#         {"$set": update_dict},
#         return_document=True,
#     )

#     if result:
#         result["id"] = str(result.pop("_id"))
#         return User(**result)
#     return None


# async def find_or_create_user(google_user: dict) -> User:
#     existing = await find_user_by_google_id(google_user["google_id"])
#     if existing:
#         return existing

#     user_create = UserCreate(
#         google_id=google_user["google_id"],
#         email=google_user["email"],
#         name=google_user.get("name"),
#         picture=google_user.get("picture"),
#     )
#     return await create_user(user_create)
