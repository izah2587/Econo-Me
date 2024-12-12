# 📊 EconoMe: Track Your Expenses & Goals 💰

Welcome to **EconoMe**, your one-stop solution for tracking expenses, setting financial goals, and making smarter financial decisions. This project helps you streamline your budgeting process, stay accountable to your goals, and take control of your financial future.

---

## 🌟 Features

✨ **User Authentication**: Secure login and signup via Auth0.  
✨ **Expense Tracking**: Add, categorize, and track your daily expenses.  
✨ **Goal Setting**: Create, update, and monitor financial goals with progress tracking.  
✨ **Daily Reminders**: Opt-in for daily email reminders to keep you on track.  
✨ **Price Comparison**: Compare prices of similar products to maximize savings.  
✨ **Responsive UI**: Beautiful, easy-to-navigate interface.

---

## 🚀 Get Started

### 🔗 Access the Deployed Version

You can access the deployed version of EconoMe here:  
👉 **[EconoMe Web App](https://econome-frontend-102803836636.us-central1.run.app)**  

Login or sign up to start managing your finances today!

---

### 🖥️ Clone the Repository Locally

If you'd like to explore or contribute to the project, follow these steps to clone and set it up locally:

#### 1️⃣ Clone the Repository
```bash
git clone https://github.com/izah2587/Econo-Me.git
cd Econo-Me
```

#### 2️⃣ Install Dependencies
Make sure you have Node.js and Python installed. Then, run the following commands:

For the frontend:
```bash
cd frontend
npm install
```

For the backend:
```bash
cd backend
pip install -r requirements.txt
```

#### 3️⃣ Set Up Environment Variables
Create a `.env` file in both the `frontend` and `backend` directories with the following keys:

**Frontend `.env`**:
```env
REACT_APP_API_BASE_URL=<your-backend-url>
REACT_APP_AUTH0_DOMAIN=<your-auth0-domain>
REACT_APP_AUTH0_CLIENT_ID=<your-auth0-client-id>
REACT_APP_AUTH0_AUDIENCE=<your-auth0-audience>
```

**Backend `.env`**:
```env
db_host=<your-database-host>
db_user=<your-database-user>
db_pass=<your-database-password>
db_name=<your-database-name>
OPENAI_API_KEY=<your-openai-api-key>
EMAIL_API=<your-mailersend-api-key>
REACT_APP_AUTH0_DOMAIN=<your-auth0-domain>
REACT_APP_AUTH0_CLIENT_ID=<your-auth0-client-id>
REACT_APP_AUTH0_AUDIENCE=<your-auth0-audience>
```

#### 4️⃣ Run the Project

**Start the Backend**:
```bash
cd backend
uvicorn main:app --reload
```

**Start the Frontend**:
```bash
cd frontend
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the app locally.

---

## 🛠️ Tech Stack

- **Frontend**: React, React Router, Auth0, Axios
- **Backend**: FastAPI, MySQL
- **Database**: MySQL
- **Email Service**: MailerSend
- **AI Integration**: OpenAI API for price comparisons

---

## 📧 Contact

For any questions or feedback, feel free to reach out at:  
📧 **economeupdate@gmail.com**

---

🎉 **Thank you for choosing EconoMe!** Let's achieve your financial goals together. 💪
