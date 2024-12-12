import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Marketplace.css';

const Marketplace = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [items, setItems] = useState([]);
  const [sortedItems, setSortedItems] = useState([]);
  const [sortOrder, setSortOrder] = useState(''); // 'asc' or 'desc'
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://econome-backend-102803836636.us-central1.run.app';

  // Fetch products based on search
  const fetchProducts = async (query) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/products/`, {
        params: { search: query },
      });
      setItems(response.data);
      setSortedItems(response.data); // Default unsorted items
    } catch (error) {
      console.error('Error fetching products:', error);
      alert('Failed to fetch products. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle sorting
  const handleSortChange = (order) => {
    setSortOrder(order);
    if (order === 'asc') {
      setSortedItems([...items].sort((a, b) => a.price - b.price));
    } else if (order === 'desc') {
      setSortedItems([...items].sort((a, b) => b.price - a.price));
    } else {
      setSortedItems(items); // Reset to original order
    }
  };

  // Handle AI Insights
  const handleGenerateAIInsights = async () => {
    try {
      const response = await axios.post(`${API_URL}/compare_prices`);
      setInsights(response.data);
    } catch (error) {
      console.error('Error generating AI insights:', error);
      alert('Failed to generate insights. Please try again.');
    }
  };

  // Filter products based on search term
  const itemsToDisplay = sortedItems.filter((item) =>
    item.product_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="marketplace-container">
      <h1 className="marketplace-title">
        Find the Best Prices with EconoMart and Our AI Buddy!
      </h1>

      {/* Search and Sort Section */}
      <div className="search-section">
        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="Search for products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button
            className="search-button"
            onClick={() => searchTerm.trim() && fetchProducts(searchTerm)}
          >
            Search
          </button>
          {/* Sorting Dropdown */}
          <select
            className="sort-dropdown"
            value={sortOrder}
            onChange={(e) => handleSortChange(e.target.value)}
          >
            <option value="">Sort by Price</option>
            <option value="asc">Lowest to Highest</option>
            <option value="desc">Highest to Lowest</option>
          </select>
        </div>
      </div>

      {/* Loading State */}
      {loading && <div className="loading-container">Loading...</div>}

      {/* Items List */}
      {!loading && (
        <div className="items-container">
          {itemsToDisplay.length > 0 ? (
            <ul className="transaction-list">
              {itemsToDisplay.map((item, index) => (
                <li key={index} className="transaction-item">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="product-link"
                  >
                    {item.product_name}
                  </a>
                  <span className="positive">${item.price.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="no-items">Search to see the list of products!</p>
          )}
        </div>
      )}

      {/* AI Insights Section */}
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
