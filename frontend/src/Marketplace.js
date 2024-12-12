import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Marketplace.css';

const Marketplace = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [items, setItems] = useState([]);
  const [sortedItems, setSortedItems] = useState([]);
  const [sortOrder, setSortOrder] = useState(''); // Sort: 'asc' or 'desc'
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000'
    : 'https://econome-backend-102803836636.us-central1.run.app';

  // Fetch products from the API
  const fetchProducts = async (query = '') => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/products/`, {
        params: { search: query },
      });
      setItems(response.data);
      setSortedItems(response.data); // Default sorted items
    } catch (error) {
      console.error('Error fetching products:', error);
      alert('Failed to fetch products. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAIInsights = async () => {
    try {
      const response = await axios.post(`${API_URL}/compare_prices`);
      setInsights(response.data);
    } catch (error) {
      console.error('Error generating AI insights:', error);
      alert('Failed to generate insights. Please try again.');
    }
  };

  const itemsToDisplay = items.filter((item) =>
    item.product_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="marketplace-container">
      <h1 className="marketplace-title">
        Find the best prices with EconoMart and our AI buddy!!
      </h1>

      <div className="search-section">
        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button className="search-button" onClick={() => searchTerm.trim() && fetchProducts(searchTerm)}>
            Search
          </button>
        </div>
      </div>

      {loading && <div className="loading-container">Loading...</div>}
{!loading && items.length > 0 && (
  <div className="items-container">
    {itemsToDisplay.length > 0 ? (
      <ul className="transaction-list">
        {itemsToDisplay.map((item, index) => (
          <li key={index} className="transaction-item">
            <span>{item.product_name}</span>
            <span className="positive">${item.price}</span>
          </li>
        ))}
      </ul>
    ) : (
      <p className="no-items">No items found.</p>
    )}
  </div>
)}

      <div className="ai-section">
        <img src="/ai_bot.jpg" alt="AI Assistant" className="ai-buddy-icon" />
        <button className="ai-insights-button" onClick={handleGenerateAIInsights}>
          GET AI INSIGHTS
        </button>
      </div>

      {insights && (
        <div className="insights-card">
          <h3>AI Insights</h3>
          <p>{insights.summary}</p>
        </div>
      )}
    </div>
  );
};

export default Marketplace;
