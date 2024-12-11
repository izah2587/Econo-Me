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
      <div className="App">
        <div className="container text-center">
          <div className="card">
            <h2>Loading...</h2>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="navbar-container">
            <Link to="/" className="brand">
              <h1>EconoMe</h1>
            </Link>
            <div className="nav-links">
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" className="nav-link">Dashboard</Link>
                  <Link to="/marketplace" className="nav-link">Marketplace</Link>
                  <Link to="/goals" className="nav-link">Goals</Link>
                  <Link to="/profile" className="nav-link">Profile</Link>
                  <button onClick={() => logout({ returnTo: window.location.origin })} className="btn btn-secondary">
                    Logout
                  </button>
                </>
              ) : (
                <button onClick={() => loginWithRedirect()} className="btn btn-primary">
                  Login/Register
                </button>
              )}
            </div>
          </div>
        </nav>

        <div className="container">
          {isAuthenticated ? (
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/marketplace" element={<Marketplace />} />
              <Route path="/goals" element={<Goals />} />
              <Route path="/" element={<Navigate to="/dashboard" />} />
            </Routes>
          ) : (
            <div className="welcome-card">
              <h1>Welcome to EconoMe</h1>
              <p>Your personal finance companion for smarter budgeting and wealth management.</p>
              <button onClick={() => loginWithRedirect()} className="btn btn-primary">
                Get Started
              </button>
            </div>
          )}
        </div>
      </div>
    </Router>
  );
};

export default App;
