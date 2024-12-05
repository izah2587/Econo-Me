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
    return <div className="App">
      <div className="container">
        <div className="card">Loading...</div>
      </div>
    </div>;
  }

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="navbar-container">
            <Link to="/" className="nav-link">
              <h1 className="text-2xl">EconoMe</h1>
            </Link>
            {isAuthenticated ? (
              <div className="nav-links">
                <Link to="/dashboard" className="nav-link">Dashboard <br/></Link>
                <Link to="/marketplace" className="nav-link">Marketplace <br/> </Link>
                <Link to="/goals" className="nav-link">Goals <br/></Link>
                <Link to="/profile" className="nav-link">Profile<br/> <br/></Link>
                <button onClick={() => logout({ returnTo: window.location.origin })} className="btn">
                  Logout
                </button>
              </div>
            ) : (
              <button onClick={() => loginWithRedirect()} className="btn">
                Login/Register
              </button>
            )}
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
            <div className="card">
              <h1 className="text-2xl">Welcome to EconoMe</h1>
              <p>Your personal finance companion for smarter budgeting and wealth management.</p>
              <button onClick={() => loginWithRedirect()} className="btn">
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
