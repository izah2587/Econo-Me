import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import { format, parseISO } from 'date-fns';

const Dashboard = () => {
    const { user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [aiReview, setAiReview] = useState('');
    const [expenseDates, setExpenseDates] = useState([]);
    const [selectedDate, setSelectedDate] = useState(null);
    const [expenses, setExpenses] = useState([]);
    const [showExpensesPopup, setShowExpensesPopup] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);

    useEffect(() => {
        const saveUserToDatabase = async () => {
          if (isAuthenticated && user) {
            try {
              const token = await getAccessTokenSilently();
              const response = await fetch('http://localhost:8000/login', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                  auth0_id: user.sub,
                  email: user.email,
                  name: user.name
                })
              });
              const data = await response.json();
              console.log('User saved to database:', data);
            } catch (error) {
              console.error('Error saving user to database:', error);
            }
          }
        };
    
        saveUserToDatabase();
        fetchExpenseDates();
    }, [isAuthenticated, user, getAccessTokenSilently]);

    const fetchExpenseDates = async () => {
        try {
            const token = await getAccessTokenSilently();
            const response = await axios.get('http://localhost:8000/expense-dates', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setExpenseDates(response.data.dates);
        } catch (error) {
            console.error('Error fetching expense dates:', error);
        }
    };

    const fetchExpenses = async (date) => {
        try {
            const token = await getAccessTokenSilently();
            const response = await axios.get(`http://localhost:8000/expenses/${date}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setExpenses(response.data.expenses);
            setSelectedDate(date);
            setShowExpensesPopup(true);
        } catch (error) {
            console.error('Error fetching expenses:', error);
        }
    };

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleUpload = async () => {
        if (!file) {
            setUploadStatus('Please select a file first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        if (isUpdating && selectedDate) {
            formData.append('update_date', selectedDate);
        }

        try {
            const token = await getAccessTokenSilently();
            const response = await axios.post('http://localhost:8000/upload-expenses', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${token}`
                }
            });
            setUploadStatus('File uploaded successfully!');
            fetchExpenseDates();
            if (selectedDate) {
                fetchExpenses(selectedDate);
            }
            setFile(null);
            setIsUpdating(false);
        } catch (error) {
            console.error('Error uploading file:', error);
            setUploadStatus('Error uploading file. Please try again.');
        }
    };

    const handleAiReview = async () => {
        try {
            const token = await getAccessTokenSilently();
            const response = await axios.get('http://localhost:8000/ai-review', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            setAiReview(response.data.analysis);
        } catch (error) {
            console.error('Error getting AI review:', error);
            setAiReview('Error getting AI review. Please try again.');
        }
    };

    const handleDateClick = (date) => {
        fetchExpenses(date);
    };

    const handleClosePopup = () => {
        setShowExpensesPopup(false);
        setSelectedDate(null);
        setExpenses([]);
    };

    const handleUpdateExpenses = () => {
        setIsUpdating(true);
        setShowExpensesPopup(false);
    };

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
        isAuthenticated && (
            <div className="dashboard-container">
                <h2>Welcome, {user.name}!</h2>
                <p>Email: {user.email}</p>
                
                <div className="upload-section">
                    <h3>Upload Expenses</h3>
                    <input type="file" onChange={handleFileChange} accept=".csv" />
                    <button onClick={handleUpload}>{isUpdating ? 'Update Expenses' : 'Upload Expenses'}</button>
                    {uploadStatus && <p>{uploadStatus}</p>}
                </div>

                <div className="expense-dates-section">
                    <h3>Expense Dates</h3>
                    <div className="date-buttons">
                        {expenseDates.map(date => (
                            <button key={date} onClick={() => handleDateClick(date)}>
                                {format(parseISO(date), 'MMM d, yyyy')}
                            </button>
                        ))}
                    </div>
                </div>

                {showExpensesPopup && (
                    <div className="expenses-popup">
                        <div className="popup-content">
                            <h3>Expenses for {format(parseISO(selectedDate), 'MMMM d, yyyy')}</h3>
                            <button onClick={handleUpdateExpenses}>Update These Expenses</button>
                            <ul>
                                {expenses.map(expense => (
                                    <li key={expense.expense_id}>
                                        ${expense.amount.toFixed(2)} - {expense.category} - {expense.description}
                                    </li>
                                ))}
                            </ul>
                            <button onClick={handleClosePopup}>Close</button>
                        </div>
                    </div>
                )}

                <div className="ai-review-section">
                    <h3>AI Review</h3>
                    <button onClick={handleAiReview}>Get AI Review</button>
                    {aiReview && <p>{aiReview}</p>}
                </div>
            </div>
        )
    );
};

export default Dashboard;