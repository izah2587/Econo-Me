import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';

const Dashboard = () => {
    const { user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [aiReview, setAiReview] = useState('');

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
    }, [isAuthenticated, user, getAccessTokenSilently]);

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

        try {
            const token = await getAccessTokenSilently();
            const response = await axios.post('http://localhost:8000/upload-expenses', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${token}`
                }
            });
            setUploadStatus('File uploaded successfully!');
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

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
        isAuthenticated && (
            <div>
                <h2>Welcome, {user.name}!</h2>
                <p>Email: {user.email}</p>
                
                <div>
                    <h3>Upload Expenses</h3>
                    <input type="file" onChange={handleFileChange} accept=".csv" />
                    <button onClick={handleUpload}>Upload</button>
                    {uploadStatus && <p>{uploadStatus}</p>}
                </div>

                <div>
                    <h3>AI Review</h3>
                    <button onClick={handleAiReview}>Get AI Review</button>
                    {aiReview && <p>{aiReview}</p>}
                </div>
            </div>
        )
    );
};

export default Dashboard;
