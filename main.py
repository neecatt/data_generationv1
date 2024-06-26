from fastapi import FastAPI, HTTPException
import json
import os
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import models
import logging
from database import engine
from sqlalchemy.orm import sessionmaker, joinedload
from models import *
from database import engine
import logging

Session = sessionmaker(bind=engine)
db_session = Session()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

# Load your data from the JSON file
data_path = r"./data/tercume.json"
try:
    if os.path.exists(data_path):
        with open(data_path, encoding='utf-8') as file:  # Ensure UTF-8 encoding
            data = json.load(file)
    else:
        data = {}
except Exception as e:
    data = {}






@app.get("/sentences")
def get_sentences():
    try:
        # Modify the query to use joinedload for the category relationship
        posts = db_session.query(Post).options(joinedload(Post.category)).order_by(Post.id).all()
        result = [
            {
                "id": post.id,
                "content": post.content,
                "likeCount": post.likeCount,
                "commentCount": post.commentCount,
                "publishedAt": post.publishedAt,
                "isApproval": post.isApproval,
                "category": {
                    "id": post.category.id,
                    "name": post.category.name,
                    "slug": post.category.slug,
                    "postCount": post.category.postCount
                }
            } for post in posts
        ]
        logging.info("Successfully fetched sentences")
        default_time = "06-26"
        current_time = datetime.now().strftime("%m-%d")
        days_between = (datetime.strptime(current_time, "%m-%d") -
                        datetime.strptime(default_time, "%m-%d")).days
        
        start_index = days_between * 135
        end_index = start_index + 135
        return result[start_index:end_index]

    except Exception as e:
        logging.error(f"Failed to fetch sentences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
    


# @app.post("/categories")
def add_categories():
    result = []
    category_id_map = {}
    category_post_count = {}
    category_count = 0
    item_count = 0  # Starting from 0 to match the requested structure

    for item in data.get("Sheet1", []):
        for category, content in item.items():
            if category != "Column1":  # Skip the Column1 key
                if category not in category_id_map:
                    # Starting category ID from 0
                    category_id_map[category] = category_count
                    category_post_count[category] = 0  # Initialize post count for new category
                    category_count += 1

                # Update post count for the category
                category_post_count[category] += 1

                result.append({
                    "id": item_count,
                    "content": content,
                    "likeCount": 0,
                    "commentCount": 0,
                    "publishedAt": datetime.now().strftime("%Y-%m-%d"),
                    "isApproval": False,
                    "category": {
                        "id": category_id_map[category],
                        "name": category,
                        "slug": category.lower().replace(" ", "-"),
                        "postCount": category_post_count[category]  # Use the updated post count
                    }
                })
                item_count += 1


    category_post_count = {cat: 0 for cat in category_id_map.keys()}
    for item in result:
        category_name = item['category']['name']
        category_post_count[category_name] += 1
    
    # Now, iterate over the category_post_count dictionary to update or insert categories in the database
    for category_name, post_count in category_post_count.items():
        # Check if the category already exists
        existing_category = db_session.query(Category).filter_by(name=category_name).first()
        if existing_category:
            # Update postCount if the category exists
            existing_category.postCount = post_count
        else:
            # Insert a new category if it does not exist
            new_category = Category(
                name=category_name,
                slug=category_name.lower().replace(" ", "-"),
                postCount=post_count
            )
            db_session.add(new_category)

    # Commit the changes to the database
    db_session.commit()

    # Close the session
    db_session.close()


    return result



# @app.post("/posts")
def add_posts():
    result = []
    item_count = 1  # Starting from 0 to match the requested structure

    for item in data.get("Sheet1", []):
        for category_name, content in item.items():
            if category_name != "Column1":  # Skip the Column1 key
                # Retrieve or create the category
                category = db_session.query(Category).filter_by(name=category_name).first()
                if not category:
                    category = Category(name=category_name, slug=category_name.lower().replace(" ", "-"))
                    db_session.add(category)
                    db_session.commit()  # Commit to retrieve the category ID

                # Prepare the post data
                post_data = {
                    "id": item_count,
                    "content": content,
                    "likeCount": 0,
                    "commentCount": 0,
                    "publishedAt": datetime.now().strftime("%Y-%m-%d"),
                    "isApproval": False,
                    "category_id": category.id  # Use the category ID from the database
                }
                result.append(post_data)
                item_count += 1

    # Insert posts data into the posts table
    for post_data in result:
        post = Post(**post_data)
        db_session.add(post)

    # Commit the changes to the database
    db_session.commit()

    # Close the session
    db_session.close()

    return result


@app.patch("/posts/{post_id}", response_model=Message, responses={200: { "content": {
                       "application/json": {
                           "example": {"message": "Post approval updated successfully."}
                       }
                   }},
                 404: { "content": {
                       "application/json": {
                           "example": {"detail": "Post Not found."}
                       }
                   }}})
def update_post(post_id: int, approval: ApprovalModel):
        post = db_session.query(Post).filter_by(id=post_id).first()
        if post:
            post.isApproval = approval.isApproval
            db_session.commit()
            db_session.close()
            return {"message": "Post approve updated successfully."}
        else:
            raise HTTPException(status_code=404, detail="Post not found")

@app.delete("/posts/{post_id}", response_model=Message, responses={200: { "content": {
                          "application/json": {
                            "example": {"message": "Post deleted successfully."}
                          }
                     }},
                  404: { "content": {
                          "application/json": {
                            "example": {"detail": "Post Not found."}
                          }
                     }}})   
def delete_post(post_id: int):
        post = db_session.query(Post).filter_by(id=post_id).first()
        if post:
            db_session.delete(post)
            db_session.commit()
            db_session.close()
            return {"message": "Post deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail="Post not found")