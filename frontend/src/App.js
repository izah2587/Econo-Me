import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import Dashboard from './Dashboard';
import Profile from './Profile';
import Marketplace from './Marketplace';
import Goals from './Goals';
import Modal from './Modal';
import './App.css';

const App = () => {
  const { loginWithRedirect, logout, isAuthenticated, isLoading, user, getAccessTokenSilently } = useAuth0();

  const [showModal, setShowModal] = useState(false); // State to control modal visibility
  const [error, setError] = useState(null); // Error state for the modal

  const BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3000'; // Use .env variable or fallback to localhost

  useEffect(() => {
    const checkEmailExists = async () => {
      if (isAuthenticated) {
        try {
          console.log('Checking if email exists...');
          const token = await getAccessTokenSilently();
          const response = await axios.get(`${BASE_URL}/api/yes_no`, {
            params: { email: user.email },
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          console.log('Response from backend:', response.data);
  
          if (!response.data.exists) {
            console.log('Email does not exist, showing modal.');
            setShowModal(true); // Show the modal if email doesn't exist
          } else {
            console.log('Email exists, not showing modal.');
          }
        } catch (error) {
          console.error('Error checking if email exists:', error);
        }
      }
    };
  
    checkEmailExists();
  }, [isAuthenticated, getAccessTokenSilently, user, BASE_URL]);
  
  const handleResponse = async (response) => {
    try {
      const token = await getAccessTokenSilently();
      await axios.post(
        `${BASE_URL}/api/yes_no`,
        {
          auth0_id: user.sub, // Auth0 user ID from the `user` object
          email: user.email, // User email from the `user` object
          response,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      console.log(`User selected: ${response}`);
      setShowModal(false); // Close the modal
    } catch (error) {
      console.error('Error saving response:', error);
      setError('Failed to save your response. Please try again later.');
    }
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <Router>
      <div className="app-container">
        {/* Landing Page for Unauthenticated Users */}
        {!isAuthenticated && (
          <div className="landing-page">
            <nav className="landing-nav">
              <Link to="/" className="logo">EconoMe</Link>
              <button onClick={() => loginWithRedirect()} className="login-button">
                Login/Signup
              </button>
            </nav>
            <div className="hero-content">
              <div className="hero-text">
                <h1>
                  Tracking Expenses,<br />
                  Hitting Goals—Sound<br />
                  Like a Plan?
                </h1>
                <button onClick={() => loginWithRedirect()} className="get-started-button">
                  Get Started
                </button>
              </div>
              <div className="hero-image">
                <img src="/finance.png" alt="Financial Planning" />
              </div>
            </div>
          </div>
        )}

        {/* App for Authenticated Users */}
        {isAuthenticated && (
          <>
            {/* Modal for Weekly Email Reminders */}
            <Modal
              show={showModal}
              onClose={() => setShowModal(false)} // Close the modal directly
              onConfirm={handleResponse} // Handle Yes/No response
              error={error}
            />

            <nav className="app-nav">
              <div className="nav-content">
                <Link to="/" className="logo">EconoMe</Link>
                <div className="nav-links">
                  <Link to="/dashboard">Dashboard</Link>
                  <Link to="/marketplace">Marketplace</Link>
                  <Link to="/goals">Goals</Link>
                  <Link to="/profile">Profile</Link>
                  <button onClick={() => logout({ returnTo: window.location.origin })} className="logout-button">
                    Logout
                  </button>
                </div>
              </div>
            </nav>
            <main className="main-content">
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/marketplace" element={<Marketplace />} />
                <Route path="/goals" element={<Goals />} />
                <Route path="/" element={<Navigate to="/dashboard" />} />
              </Routes>
            </main>
          </>
        )}
      </div>
    </Router>
  );
};

export default App;
