import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import { format, parseISO } from 'date-fns';
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, TooltipProps } from 'recharts';
import './Dashboard.css';

const Dashboard = () => {
    const DEFAULT_WEEKLY_DATA = [
        { category: 'Food', percentage: 35 },
        { category: 'Utilities', percentage: 25 },
        { category: 'Entertainment', percentage: 20 },
        { category: 'Other', percentage: 15 }
    ];

    const DEFAULT_DAILY_DATA = [
        { category: 'Food', value: 40 },
        { category: 'Shopping', value: 30 },
        { category: 'Transport', value: 20 },
        { category: 'Other', value: 10 }
    ];

    const { user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [aiReview, setAiReview] = useState('');
    const [expenseDates, setExpenseDates] = useState([]);
    const [selectedDate, setSelectedDate] = useState(null);
    const [expenses, setExpenses] = useState([]);
    const [showExpensesPopup, setShowExpensesPopup] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [weeklyData, setWeeklyData] = useState(DEFAULT_WEEKLY_DATA);
    const [dailyData, setDailyData] = useState(DEFAULT_DAILY_DATA);

    const API_URL = window.location.hostname === 'localhost' 
        ? 'http://localhost:8000'
        : 'https://econome-backend-102803836636.us-central1.run.app';

    const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];

    const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="custom-tooltip" style={{ backgroundColor: '#fff', padding: '5px', border: '1px solid #ccc' }}>
                    <p className="label">{`${data.category} : ${data.value}%`}</p>
                </div>
            );
        }
        return null;
    };


    useEffect(() => {
        const fetchData = async () => {
            if (isAuthenticated && user) {
                try {
                    const token = await getAccessTokenSilently();
                    
                    // Save user to database
                    await fetch(`${API_URL}/login`, {
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

                    // Fetch expense dates
                    const datesResponse = await axios.get(`${API_URL}/expense-dates`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    setExpenseDates(datesResponse.data.dates);

                    // Fetch weekly averages
                    const weeklyResponse = await axios.get(`${API_URL}/weekly-averages`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    setWeeklyData(weeklyResponse.data.weekly_averages.length > 0 
                        ? weeklyResponse.data.weekly_averages 
                        : DEFAULT_WEEKLY_DATA);

                    // Fetch daily average
                    const dailyResponse = await axios.get(`${API_URL}/daily-average`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    setDailyData(dailyResponse.data.daily_averages.length > 0
                        ? dailyResponse.data.daily_averages 
                        : DEFAULT_DAILY_DATA);

                } catch (error) {
                    console.error('Error fetching data:', error);
                }
            }
        };

        fetchData();
    }, [isAuthenticated, user, getAccessTokenSilently]);

    const fetchExpenseDates = async () => {
        try {
            const token = await getAccessTokenSilently();
            const response = await axios.get(`${API_URL}/expense-dates`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            console.log('Fetched expense dates:', response.data.dates);
            setExpenseDates(response.data.dates);
        } catch (error) {
            console.error('Error fetching expense dates:', error);
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

        console.log('Starting file upload:', file.name);

        const formData = new FormData();
        formData.append('file', file);

        if (isUpdating && selectedDate) {
            formData.append('update_date', selectedDate);
        }

        try {
            const token = await getAccessTokenSilently();
            console.log('Token acquired, sending request to:', `${API_URL}/upload-expenses`);
            const response = await axios.post(`${API_URL}/upload-expenses`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${token}`
                }
            });
            console.log('Upload response:', response.data);
            setUploadStatus('File uploaded successfully!');
            await fetchExpenseDates();
            if (selectedDate) {
                await fetchExpenses(selectedDate);
            }
            setFile(null);
            setIsUpdating(false);
        } catch (error) {
            console.error('Error uploading file:', error);
            setUploadStatus(`Error uploading file: ${error.message}`);
        }
    };

    const handleAiReview = async () => {
        try {
            const token = await getAccessTokenSilently();
            const response = await axios.get(`${API_URL}/ai-review`, {
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

    const fetchExpenses = async (date) => {
        try {
            const token = await getAccessTokenSilently();
            const response = await axios.get(`${API_URL}/expenses/${date}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setExpenses(response.data.expenses);
            setSelectedDate(date);
            setShowExpensesPopup(true);
            console.log('Fetched expenses:', response.data.expenses);
        } catch (error) {
            console.error('Error fetching expenses:', error);
        }
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
        return <div className="loading">Loading...</div>;
    }

    return (
        isAuthenticated && (
            <div className="dashboard-container">
                <main className="main-content">
                    <div className="left-section">
                        <div className="ai-section">
                            <img src="/ai_bot.jpg" alt="AI Bot" className="ai-bot" />
                            <button className="ai-review-button" onClick={handleAiReview}>
                                GET AI REVIEW!
                            </button>
                        </div>
                        
                        {aiReview && (
                            <div className="ai-response">
                                <p>{aiReview}</p>
                            </div>
                        )}

                        <div className="charts-section">
                            <div className="weekly-averages">
                                <h2>YOUR WEEKLY AVERAGES</h2>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart
                                        layout="vertical"
                                        data={weeklyData}
                                        margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" unit="%" />
                                        <YAxis dataKey="category" type="category" />
                                        <Tooltip />
                                        <Bar dataKey="percentage" fill="#45B7D1" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="daily-average">
                                <h2>Daily Average</h2>
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={dailyData}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            outerRadius={100}
                                            fill="#8884d8"
                                            dataKey="value"
                                            nameKey="category"
                                        >
                                            {dailyData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    <div className="right-section">
                        <div className="dates-section">
                            {expenseDates.map(date => (
                                <a
                                    key={date}
                                    href="#"
                                    className="date-link"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        handleDateClick(date);
                                    }}
                                >
                                    {format(parseISO(date), 'dd-MM-yyyy')}
                                </a>
                            ))}
                        </div>
                        <div className="upload-section">
                            <label className="block w-full">
                                <input
                                    type="file"
                                    onChange={handleFileChange}
                                    accept=".csv"
                                    className="hidden"
                                />
                                <span className="block w-full text-center bg-[#008B9C] text-white px-6 py-3 rounded-lg cursor-pointer hover:bg-[#007A8A] transition-colors font-semibold">
                                    {file ? `Selected: ${file.name}` : '+ Select Expenses File'}
                                </span>
                            </label>
                            {file && (
                                <button 
                                    onClick={handleUpload} 
                                    className="upload-expenses-button w-full bg-[#7BC8A4] hover:bg-[#6AB393] text-white px-6 py-3 rounded-lg transition-colors font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed"
                                    disabled={!file}
                                >
                                    Upload Expenses
                                </button>
                            )}
                            {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
                        </div>
                        <div className="navigation-arrows">
                            <button className="nav-arrow">←</button>
                            <button className="nav-arrow">→</button>
                        </div>
                    </div>
                </main>

                {showExpensesPopup && (
                    <div className="popup-overlay">
                        <div className="popup-content">
                            <h3>Expenses for {format(parseISO(selectedDate), 'MMMM d, yyyy')}</h3>
                            <div className="expenses-list">
                                {expenses.map(expense => (
                                    <div key={expense.expense_id} className="expense-item">
                                        <span className="amount">${expense.amount.toFixed(2)}</span>
                                        <span className="category">{expense.category}</span>
                                        <span className="description">{expense.description}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="popup-buttons">
                                <button className="update-button" onClick={handleUpdateExpenses}>
                                    Update These Expenses
                                </button>
                                <button className="close-button" onClick={handleClosePopup}>
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        )
    );
};

export default Dashboard;

