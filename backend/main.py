from fastapi import FastAPI, HTTPException, Request, Depends, File, UploadFile
from io import StringIO
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
from dotenv import load_dotenv
from pydantic import BaseModel
import requests
import os
import mysql.connector
from mysql.connector import Error
import csv
import re
import pandas as pd
import openai
from datetime import date,  datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi.params import Query
from typing import Optional
from collections import defaultdict


# Load environment variables
load_dotenv()

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("REACT_APP_AUTH0_DOMAIN", "dev-xgm0lup6iwjt0i8k.us.auth0.com")
AUTH0_CLIENT_ID = os.getenv("REACT_APP_AUTH0_CLIENT_ID", "h6VQMvtBnAn3ApXwVjiWcQSsGSHdk5hl")
AUTH0_AUDIENCE = os.getenv("REACT_APP_AUTH0_AUDIENCE", "EKtYAN3Rd7RCVsNhoAPLCuZ0j9AbQoA1")
ALGORITHMS = ["RS256"]

# Database configuration
DB_HOST = os.getenv("db_host")
DB_NAME = os.getenv("db_name")
DB_USER = os.getenv("db_user")
DB_PASS = os.getenv("db_pass")

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://econome-frontend-102803836636.us-central1.run.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for token
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{AUTH0_DOMAIN}/authorize",
    tokenUrl=f"https://{AUTH0_DOMAIN}/oauth/token",
)

# Pydantic models
class UserLogin(BaseModel):
    auth0_id: str
    email: str
    name: str

class Goal(BaseModel):
    goal_id: int
    status: str
    set_date: date
    due_date: date
    goal_type: Optional[str] = None
    current_amount: float
    target_amount: float
    auth0_id: str
    user_id: int

class GoalCreate(BaseModel):
    title: str
    description: str
    target_amount: float
    current_amount: float
    deadline: date

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class Expense(BaseModel):
    date: date
    amount: float
    category: str
    user_id: int

class YesNoRequest(BaseModel):
    email: str
    response: str  # Must be 'Yes' or 'No'
    auth0_id: str

# Database connection helper
def create_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        if conn.is_connected():
            print("Connected to the database")
            return conn
    except Error as error:
        raise HTTPException(status_code=500, detail=f"Database connection error: {error}")

# Utility to verify JWT
async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is expired")
    except jwt.JWTClaimsError:
        raise HTTPException(status_code=401, detail="Invalid claims")
    except Exception:
        raise HTTPException(status_code=401, detail="Unable to parse authentication token")
    raise HTTPException(status_code=401, detail="Unable to find appropriate key")


@app.get("/")
async def root():
    return {"message": "Welcome to Econo-Me!"}


# Login endpoint
@app.post("/login")
async def login(user_data: UserLogin, token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    print("hitting login endpoint")
    
    if not all([user_data.auth0_id, user_data.email, user_data.name]):
        raise HTTPException(status_code=400, detail="Incomplete user information")

    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Check if the user already exists
        cursor.execute("SELECT * FROM Users WHERE auth0_id = %s", (user_data.auth0_id,))
        user = cursor.fetchone()
        print("does user exist:", user)

        if not user:
            print("User does not exist")
            print(user_data)
            # Insert new user into the database
            cursor.execute(
                "INSERT INTO Users (auth0_id, name, email) VALUES (%s, %s, %s)",
                (user_data.auth0_id, user_data.name, user_data.email),
            )
            print("User inserted")
            conn.commit()
            cursor.execute("SELECT * FROM Users WHERE auth0_id = %s", (user_data.auth0_id,))
            user = cursor.fetchone()
            print(user)

        return {"message": "Login successful", "user": user}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Profile endpoint
@app.get("/profile")
async def profile(token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    print(user_payload)
    # fetch user data from the database
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user = cursor.fetchone()
        print(user)
        return {"user": user}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



# Function to upload data from CSV to the database
def upload_csv_data():
    csv_file_paths = [
        "trader_joes_products.csv",  # Trader Joe's products
        "scraped_products.csv"       # Target products
    ]

    try:
        conn = create_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed.")
        cursor = conn.cursor()

        for csv_file_path in csv_file_paths:
            if not os.path.exists(csv_file_path):
                print(f"CSV file '{csv_file_path}' not found, skipping.")
                continue

            print(f"Processing file: {csv_file_path}")
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Clean the 'price' field to remove any non-numeric characters
                    price_str = row['price']
                    cleaned_price = re.sub(r'[^\d.]', '', price_str)

                    # Convert the cleaned price to a float
                    try:
                        price = float(cleaned_price)
                    except ValueError:
                        print(f"Invalid price format for product {row['product_name']}: {price_str}")
                        continue

                    # Check for existing entry to avoid duplicates
                    cursor.execute("""
                        SELECT COUNT(*) FROM Marketplace WHERE product_name = %s AND store_name = %s
                    """, (row['product_name'], row['store_name']))
                    count = cursor.fetchone()[0]

                    if count == 0:
                        # Insert new product
                        cursor.execute("""
                            INSERT INTO Marketplace (product_name, price, store_name)
                            VALUES (%s, %s, %s)
                        """, (row['product_name'], price, row['store_name']))
                    else:
                        # Update existing product
                        cursor.execute("""
                            UPDATE Marketplace
                            SET price = %s
                            WHERE product_name = %s AND store_name = %s
                        """, (price, row['product_name'], row['store_name']))

        conn.commit()
        print("CSV data uploaded successfully.")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint to fetch products
@app.get("/products/")
async def get_products(search: str = None):
    try:
        conn = create_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed.")
        cursor = conn.cursor(dictionary=True)

        if search:
            query = "SELECT * FROM Marketplace WHERE LOWER(product_name) LIKE %s"
            cursor.execute(query, (f"%{search.lower()}%",))
        else:
            query = "SELECT * FROM Marketplace"
            cursor.execute(query)

        products = cursor.fetchall()
        return products
    except Error as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Function to read products from a CSV file using Pandas
def read_products_from_csv(file_path: str) -> pd.DataFrame:
    try:
        # Load the CSV into a DataFrame
        df = pd.read_csv(file_path)

        # Clean the 'price' column by removing non-numeric characters and converting it to float
        df['price'] = df['price'].replace({r'[^\d.]': ''}, regex=True)  # Keep only digits and decimal points
        df['price'] = pd.to_numeric(df['price'], errors='coerce')  # Convert to float, invalid values become NaN

        # Remove rows where price is NaN (invalid data)
        df = df.dropna(subset=['price'])

        return df[['product_name', 'price']]  # Return only the necessary columns
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file '{file_path}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Price comparison function using OpenAI
def generate_price_comparison_summary(target_df: pd.DataFrame, trader_joes_df: pd.DataFrame) -> str:
    # Convert DataFrames to a string format for OpenAI
    target_products_str = target_df.to_dict(orient='records')
    trader_joes_products_str = trader_joes_df.to_dict(orient='records')

    prompt = f"""
    You are a price comparison assistant. I will provide you with product prices from two stores, Target and Trader Joe's.

    Please compare the prices of the following products between the two stores. You do not need to rely on exact product names but instead use your understanding to evaluate if two products are similar. For example, "Red Onion" and "Onion" can be considered the same. Use keywords, context, and common product categories to determine similarity. If two products are different but belong to the same category (e.g., onions, tomatoes, garlic, herbs), treat them as similar.

    If a product is found in both stores, calculate the percentage price difference. If a product is only found in one store, ignore it in the comparison.

    Please provide a general overall summary comparing the two stores in plain text format without Markdown:
    - Which store generally has better prices (Target or Trader Joe's)?
    - What is the approximate percentage difference in prices across all products compared (if applicable)?

    Ensure that the response is brief and formatted for easy readability in a UI card component.

    Here is the data you should consider:

    Target Products:
    {target_products_str}

    Trader Joe's Products:
    {trader_joes_products_str}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a price comparison assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("API Call Failed:", str(e))
        return "Failed to generate price comparison summary."


# API endpoint to compare prices between Target and Trader Joe's
@app.post("/compare_prices")
async def compare_prices():
    # Define file paths for the CSV files
    target_file_path = "scraped_products.csv"  # Path to your Target CSV file
    trader_joes_file_path = "trader_joes_products.csv"  # Path to your Trader Joe's CSV file

    # Read products from both CSV files using Pandas
    target_df = read_products_from_csv(target_file_path)
    trader_joes_df = read_products_from_csv(trader_joes_file_path)

    # Generate the price comparison summary using OpenAI
    try:
        summary = generate_price_comparison_summary(target_df, trader_joes_df)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# for the charts...

# GOALS

@app.post("/goals")
async def create_goal(request: Request, goal: GoalCreate, token: str = Depends(oauth2_scheme)):
    print("Reaching create_goal function")
    body = await request.json()
    print(f"Received request body: {body}")
    print(f"Parsed goal: {goal}")
    
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # First, get the user_id from the Users table
        user_query = "SELECT user_id FROM Users WHERE auth0_id = %s"
        cursor.execute(user_query, (user_payload["sub"],))
        user_result = cursor.fetchone()
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user_result['user_id']
        
        # Now insert into Goals table
        query = """
        INSERT INTO Goals (status, set_date, due_date, goal_type, target_amount, current_amount, auth0_id, user_id, title, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        values = (
            'active',
            datetime.now().date(),
            goal.deadline,
            None,  # goal_type is not provided in GoalCreate
            goal.target_amount,
            goal.current_amount or 0,
            user_payload["sub"],
            user_id,  # Now using the fetched user_id
            goal.title,
            goal.description
        )
        cursor.execute(query, values)
        conn.commit()
        goal_id = cursor.lastrowid
        return {"message": "Goal created successfully", "goal_id": goal_id}
    except Error as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/goals")
async def get_goals(status: Optional[str] = Query(None), token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Goals WHERE auth0_id = %s"
        values = [user_payload["sub"]]
        if status:
            query += " AND status = %s"
            values.append(status)
        query += " ORDER BY due_date ASC"
        cursor.execute(query, tuple(values))
        goals = cursor.fetchall()
        return {"goals": goals}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.put("/goals/{goal_id}")
async def update_goal(goal_id: int, goal: GoalUpdate, token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # Check if the goal belongs to the user
        cursor.execute("SELECT * FROM Goals WHERE goal_id = %s AND auth0_id = %s", (goal_id, user_payload["sub"]))
        existing_goal = cursor.fetchone()
        if not existing_goal:
            raise HTTPException(status_code=404, detail="Goal not found or does not belong to the user")
        
        # Prepare update query
        update_fields = []
        values = []
        for field, value in goal.dict(exclude_unset=True).items():
            update_fields.append(f"{field} = %s")
            values.append(value)
        
        # Check if current_amount equals target_amount and update the status
        if 'current_amount' in goal.dict(exclude_unset=True):
            new_current = goal.current_amount
            if new_current == existing_goal['target_amount']:
                update_fields.append("status = %s")
                values.append("completed")

        if update_fields:
            query = f"UPDATE Goals SET {', '.join(update_fields)} WHERE goal_id = %s"
            values.append(goal_id)
            print(f"Executing query: {query} with values: {values}")
            cursor.execute(query, tuple(values))
            conn.commit()

        return {"message": "Goal updated successfully"}
    except Error as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.delete("/goals/{goal_id}")
async def delete_goal(goal_id: int, token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # First, check if the goal belongs to the user
        cursor.execute("SELECT * FROM Goals WHERE goal_id = %s AND auth0_id = %s", (goal_id, user_payload["sub"]))
        existing_goal = cursor.fetchone()
        if not existing_goal:
            raise HTTPException(status_code=404, detail="Goal not found or does not belong to the user")
        
        # Delete the goal
        cursor.execute("DELETE FROM Goals WHERE goal_id = %s", (goal_id,))
        conn.commit()
        return {"message": "Goal deleted successfully"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.post("/api/yes_no")
async def save_yes_no(data: YesNoRequest):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO yes_no (auth0_id, email, response)
            VALUES (%s, %s, %s)
        """
        values = (data.auth0_id, data.email, data.response)
        cursor.execute(sql, values)
        conn.commit()
        return {"message": "Response saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/yes_no")
async def check_email_exists(email: str = Query(...)):
    print(f"Checking if email exists: {email}")
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT 1 FROM yes_no WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        # If a record exists, return exists=True
        if result:
            return {"exists": True}
        return {"exists": False}
    except Error as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



# EXPENSES

def categorize_expense(description: str) -> str:
    # This is a simple categorization. You might want to use a more sophisticated method or AI for better categorization.
    categories = {
        'grocery': ['grocery', 'supermarket', 'food'],
        'transport': ['transport', 'gas', 'fuel', 'uber', 'taxi'],
        'utilities': ['utility', 'electric', 'water', 'internet'],
        'entertainment': ['restaurant', 'cinema', 'theater', 'streaming'],
        'shopping': ['purchase', 'buy', 'amazon'],
    }
    
    description = description.lower()
    for category, keywords in categories.items():
        if any(keyword in description for keyword in keywords):
            return category
    return 'other'

@app.post("/upload-expenses")
async def upload_expenses(
    file: UploadFile = File(...),
    update_date: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    user_payload = await verify_token(token)
    content = await file.read()
    df = pd.read_csv(StringIO(content.decode('utf-8')))
    
    # Validate that all dates in the file are the same
    if 'date' not in df.columns:
        raise HTTPException(status_code=400, detail="CSV file must contain a 'date' column")
    
    # Convert dates to consistent format
    df['date'] = pd.to_datetime(df['date']).dt.date
    unique_dates = df['date'].unique()
    
    if len(unique_dates) > 1:
        raise HTTPException(
            status_code=400, 
            detail="All expenses in the file must be for the same date"
        )
    
    file_date = unique_dates[0]
    
    # If updating existing date, validate it matches
    if update_date:
        update_date = datetime.strptime(update_date, '%Y-%m-%d').date()
        if file_date != update_date:
            raise HTTPException(
                status_code=400,
                detail=f"File contains expenses for {file_date}, but updating date {update_date}"
            )
    
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT user_id FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_result['user_id']
        
        # If updating, delete existing expenses for that date
        if update_date:
            cursor.execute(
                "DELETE FROM Expenses WHERE user_id = %s AND date = %s",
                (user_id, update_date)
            )
        
        # Insert expenses
        for _, row in df.iterrows():
            category = categorize_expense(row['description'])
            expense = Expense(
                date=file_date,
                amount=float(row['amount']),
                category=category,
                user_id=user_id
            )
            query = """
                INSERT INTO Expenses (date, amount, category, user_id)
                VALUES (%s, %s, %s, %s)
            """
            values = (expense.date, expense.amount, expense.category, expense.user_id)
            cursor.execute(query, values)
        
        conn.commit()
        return {"message": "Expenses uploaded successfully"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.get("/expense-dates")
async def get_expense_dates(token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT user_id FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_result['user_id']
        
        # Get distinct dates of expenses
        cursor.execute("SELECT DISTINCT date FROM Expenses WHERE user_id = %s ORDER BY date DESC", (user_id,))
        dates = cursor.fetchall()
        
        return {"dates": [date['date'].isoformat() for date in dates]}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.get("/expenses/{date}")
async def get_expenses_by_date(date: str, token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT user_id FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_result['user_id']
        
        # Get expenses for the specified date
        cursor.execute("SELECT * FROM Expenses WHERE user_id = %s AND date = %s", (user_id, date))
        expenses = cursor.fetchall()
        
        return {"expenses": expenses}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.put("/expenses/{expense_id}")
async def update_expense(expense_id: int, expense: Expense, token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT user_id FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_result['user_id']
        
        # Update the expense
        query = "UPDATE Expenses SET date = %s, amount = %s, category = %s WHERE expense_id = %s AND user_id = %s"
        values = (expense.date, expense.amount, expense.category, expense_id, user_id)
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found or does not belong to the user")
        
        return {"message": "Expense updated successfully"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def calculate_average_daily_spending(expenses: List[Dict]) -> float:
    if not expenses:
        return 0
    total_spending = sum(expense['amount'] for expense in expenses)
    date_range = (max(expense['date'] for expense in expenses) - min(expense['date'] for expense in expenses)).days + 1
    return total_spending / date_range

def calculate_goal_alignment(expenses: List[Dict], goals: List[Dict]) -> float:
    if not goals:
        return 100  # If there are no goals, we consider the user 100% aligned
    
    total_daily_target = sum(goal['target_amount'] / (goal['due_date'] - datetime.now().date()).days for goal in goals if goal['due_date'] > datetime.now().date())
    avg_daily_spending = calculate_average_daily_spending(expenses)
    
    if total_daily_target == 0:
        return 100 if avg_daily_spending == 0 else 0
    
    alignment = (1 - min(1, max(0, (avg_daily_spending - total_daily_target) / total_daily_target))) * 100
    return round(alignment, 2)

@app.get("/ai-review")
async def get_ai_review(token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT user_id FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_result['user_id']
        
        # Get user's expenses for the last 30 days
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        cursor.execute("SELECT * FROM Expenses WHERE user_id = %s AND date >= %s ORDER BY date DESC", (user_id, thirty_days_ago))
        expenses = cursor.fetchall()
        
        # Get user's active goals
        cursor.execute("SELECT * FROM Goals WHERE user_id = %s AND status = 'active'", (user_id,))
        goals = cursor.fetchall()
        
        # Calculate average daily spending and goal alignment
        avg_daily_spending = calculate_average_daily_spending(expenses)
        goal_alignment = calculate_goal_alignment(expenses, goals)
        
        # Prepare data for OpenAI
        expenses_str = "\n".join([f"Date: {e['date']}, Amount: ${e['amount']:.2f}, Category: {e['category']}" for e in expenses])
        goals_str = "\n".join([f"Goal: {g['title']}, Target: ${g['target_amount']:.2f}, Deadline: {g['due_date']}" for g in goals])
        
        prompt = f"""
        Analyze the following user's expenses and financial goals:

        Average Daily Spending: ${avg_daily_spending:.2f}
        Current Goal Alignment: {goal_alignment}%

        Expenses (last 30 days):
        {expenses_str}

        Financial Goals:
        {goals_str}

        Please provide a comprehensive analysis of the user's spending habits in relation to their financial goals. 
        Your response should include:

        1. A brief overview of their current financial situation.
        2. An explanation of their goal alignment percentage and what it means. calculate the goal alignment and give a specific value like Goal Alignment: 75%. explain how it is calculated as well.
        3. Specific recommendations for each goal, considering their current spending habits.
        4. A checklist of 3-5 actionable items to improve their financial situation.
        5. Encouragement and positive reinforcement for any good financial habits observed.

        Format your response as follows:

        Overview: [Your analysis here]

        Goal Alignment: [Explanation of the {goal_alignment}% alignment]

        Goal-specific Recommendations:
        [List each goal and provide specific advice]

        Action Checklist:
        - [Action item 1]
        - [Action item 2]
        - [Action item 3]
        - [Action item 4 (if applicable)]
        - [Action item 5 (if applicable)]

        Positive Reinforcement: [Encouragement and recognition of good habits]

        Make sure to address the user in your response. Address the user as "you"
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial advisor assistant. Provide clear, actionable advice."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {"analysis": response['choices'][0]['message']['content'].strip()}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Upload CSV data at startup
@app.on_event("startup")
async def startup_event():
    print("Starting CSV upload...")
    upload_csv_data()
    print("CSV upload completed.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)