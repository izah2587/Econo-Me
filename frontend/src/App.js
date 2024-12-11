import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import Dashboard from './Dashboard';
import Profile from './Profile';
import Marketplace from './Marketplace';
import Goals from './Goals';
import './App.css';

const App = () => {
  const { loginWithRedirect, logout, isAuthenticated, isLoading } = useAuth0();

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

        {isAuthenticated && (
          <>
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