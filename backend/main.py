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
from datetime import date,  datetime
from typing import Optional, List
from fastapi.params import Query


# Load environment variables
load_dotenv()

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-xgm0lup6iwjt0i8k.us.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "h6VQMvtBnAn3ApXwVjiWcQSsGSHdk5hl")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://api.econome.com")
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
    allow_origins=["http://localhost:3000"],
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
    current_amount: Optional[float] = None
    target_amount: float
    auth0_id: str
    user_id: int

class GoalCreate(BaseModel):
    title: str
    description: str
    target_amount: float
    deadline: date

class GoalUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    goal_type: Optional[str] = None
    current_amount: Optional[float] = None
    target_amount: Optional[float] = None

class Expense(BaseModel):
    date: date
    amount: float
    category: str
    user_id: int

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

    If a product is found in both stores, calculate the percentage price difference. If a product is only found in one store, try to find a similar product from the other store and treat it as part of the same category. If no equivalent product is found in the other store, ignore it in your comparison.

    For the summary, display 5 example products that are available in both stores, showing their price differences and the percentage difference between them. Each example should include the following:
    - Product Name
    - Target Price
    - Trader Joe's Price
    - Percentage Price Difference (rounded to 2 decimal places)

    Ensure that the examples reflect a range of price differences:
    1. One example where Target is more expensive.
    2. One example where Trader Joe's is more expensive.
    3. One example where the prices are equal.
    4. The other examples should show diverse products with varied price differences.

    Please also provide a general overall summary comparing the two stores:
    - Which store generally has better prices (Target or Trader Joe's)?
    - What is the approximate percentage difference in prices across all products compared (if applicable)?

    Here is the data you should consider:

    Target Products:
    {target_products_str}

    Trader Joe's Products:
    {trader_joes_products_str}

    Please provide the results in an HTML format. Use the following structure:

    <h3>Example Products:</h3>
    <ul>
        <li><strong>Product Name:</strong> Product1 <br> <strong>Target Price:</strong> $5.89 <br> <strong>Trader Joe's Price:</strong> $2.29 <br> <strong>Percentage Price Difference:</strong> 61.16%</li>
        <!-- Add other products here -->
    </ul>

    <h3>Overall Summary</h3>
    <p>Trader Joe's generally has better prices as seen in the provided examples. The average savings when shopping at Trader Joe's compared to Target is approximately 33.05%.</p>
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
        INSERT INTO Goals (status, set_date, due_date, goal_type, target_amount, auth0_id, user_id, title, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            'active',
            datetime.now().date(),
            goal.deadline,
            None,  # goal_type is not provided in GoalCreate
            goal.target_amount,
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
        # First, check if the goal belongs to the user
        cursor.execute("SELECT * FROM Goals WHERE goal_id = %s AND auth0_id = %s", (goal_id, user_payload["sub"]))
        existing_goal = cursor.fetchone()
        if not existing_goal:
            raise HTTPException(status_code=404, detail="Goal not found or does not belong to the user")
        
        # Update the goal
        update_fields = []
        values = []
        for field, value in goal.dict(exclude_unset=True).items():
            update_fields.append(f"{field} = %s")
            values.append(value)
        
        if update_fields:
            query = f"UPDATE Goals SET {', '.join(update_fields)} WHERE goal_id = %s"
            values.append(goal_id)
            cursor.execute(query, tuple(values))
            conn.commit()
        
        return {"message": "Goal updated successfully"}
    except Error as e:
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
async def upload_expenses(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    user_payload = await verify_token(token)
    content = await file.read()
    df = pd.read_csv(StringIO(content.decode('utf-8')))
    
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT user_id FROM Users WHERE auth0_id = %s", (user_payload["sub"],))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_result['user_id']
        
        # Insert expenses
        for _, row in df.iterrows():
            category = categorize_expense(row['description'])
            expense = Expense(date=row['date'], amount=row['amount'], category=category, user_id=user_id)
            query = "INSERT INTO Expenses (date, amount, category, user_id) VALUES (%s, %s, %s, %s)"
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
        
        # Get user's expenses
        cursor.execute("SELECT * FROM Expenses WHERE user_id = %s ORDER BY date DESC LIMIT 30", (user_id,))
        expenses = cursor.fetchall()
        
        # Get user's goals
        cursor.execute("SELECT * FROM Goals WHERE user_id = %s AND status = 'active'", (user_id,))
        goals = cursor.fetchall()
        
        # Prepare data for OpenAI
        expenses_str = "\n".join([f"Date: {e['date']}, Amount: ${e['amount']}, Category: {e['category']}" for e in expenses])
        goals_str = "\n".join([f"Goal: {g['title']}, Target: ${g['target_amount']}, Deadline: {g['due_date']}" for g in goals])
        
        prompt = f"""
        Analyze the following user's expenses and financial goals:

        Expenses:
        {expenses_str}

        Financial Goals:
        {goals_str}

        Please provide a brief analysis of the user's spending habits in relation to their financial goals. 
        Offer suggestions on how they can better align their spending with their goals. 
        If they're doing well, offer encouragement and tips to maintain their good habits.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial advisor assistant."},
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
    uvicorn.run(app, host="0.0.0.0", port=8000)