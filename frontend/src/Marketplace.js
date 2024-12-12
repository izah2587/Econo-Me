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

  // Determine the API URL based on the current hostname
  const API_URL =
    window.location.hostname === 'localhost'
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

  useEffect(() => {
    fetchProducts();
  }, []);

  // Sort the items based on the selected order
  const handleSortChange = (order) => {
    setSortOrder(order);
    if (order === 'asc') {
      setSortedItems([...items].sort((a, b) => a.price - b.price));
    } else if (order === 'desc') {
      setSortedItems([...items].sort((a, b) => b.price - a.price));
    } else {
      setSortedItems(items); // Reset to the default order
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

  const filteredItems = searchTerm
    ? sortedItems.filter((item) =>
        item.product_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : sortedItems;

  return (
    <div>
      <div className="search-container">
        <input
          type="text"
          className="input"
          placeholder="Search for items..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <button className="btn" onClick={() => fetchProducts(searchTerm)}>
          Search
        </button>
        <select
          className="input"
          value={sortOrder}
          onChange={(e) => handleSortChange(e.target.value)}
        >
          <option value="">Sort by Price</option>
          <option value="asc">Lowest to Highest</option>
          <option value="desc">Highest to Lowest</option>
        </select>
      </div>

      {loading ? (
        <div className="card">Loading...</div>
      ) : (
        <div className="items-container">
          {filteredItems.length > 0 ? (
            <ul className="transaction-list">
              {filteredItems.map((item, index) => (
                <li key={index} className="transaction-item">
                  <span>{item.product_name}</span>
                  <span className="positive">${item.price.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No items found.</p>
          )}
        </div>
      )}

      <button className="btn" onClick={handleGenerateAIInsights}>
        Generate AI Insights
      </button>

      {insights && (
        <div className="card">
          <h3 className="text-2xl">AI Insights</h3>
          <p>{insights.summary}</p>
        </div>
      )}
    </div>
  );
};

export default Marketplace;
