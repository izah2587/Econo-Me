import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth0 } from '@auth0/auth0-react';

const Goals = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [goals, setGoals] = useState({ active: [], completed: [] });
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    target_amount: '',
    deadline: '',
  });
  const [error, setError] = useState(null);

  const fetchGoals = async () => {
    try {
      const token = await getAccessTokenSilently();
      const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/goals`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const allGoals = response.data.goals;
      setGoals({
        active: allGoals.filter(goal => goal.status === 'active'),
        completed: allGoals.filter(goal => goal.status === 'completed'),
      });
      setError(null);
    } catch (error) {
      console.error('Error fetching goals:', error);
      setError('Failed to fetch goals. Please try again later.');
    }
  };

  useEffect(() => {
    fetchGoals();
  }, [getAccessTokenSilently]);

  const handleInputChange = (e) => {
    setNewGoal({ ...newGoal, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = await getAccessTokenSilently();
      const goalData = {
        title: newGoal.title,
        description: newGoal.description,
        target_amount: parseFloat(newGoal.target_amount),
        deadline: newGoal.deadline
      };
      console.log('Sending goal data:', goalData);
      await axios.post(`${process.env.REACT_APP_API_BASE_URL}/goals`, goalData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
      });
      setNewGoal({ title: '', description: '', target_amount: '', deadline: '' });
      fetchGoals();
    } catch (error) {
      console.error('Error creating goal:', error);
      setError('Failed to create goal. Please try again.');
    }
  };

  const handleDelete = async (goalId) => {
    try {
      const token = await getAccessTokenSilently();
      await axios.delete(`${process.env.REACT_APP_API_BASE_URL}/goals/${goalId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchGoals();
    } catch (error) {
      console.error('Error deleting goal:', error);
      setError('Failed to delete goal. Please try again.');
    }
  };

  return (
    <div className="goals-container">
      <h2>Goals</h2>
      {error && <div className="error">{error}</div>}
      
      <form onSubmit={handleSubmit} className="new-goal-form">
        <h3>Set New Goal</h3>
        <input
          type="text"
          name="title"
          value={newGoal.title}
          onChange={handleInputChange}
          placeholder="Goal Title"
          required
        />
        <textarea
          name="description"
          value={newGoal.description}
          onChange={handleInputChange}
          placeholder="Goal Description"
          required
        />
        <input
          type="number"
          name="target_amount"
          value={newGoal.target_amount}
          onChange={handleInputChange}
          placeholder="Target Amount"
          required
        />
        <input
          type="date"
          name="deadline"
          value={newGoal.deadline}
          onChange={handleInputChange}
          required
        />
        <button type="submit">Create Goal</button>
      </form>

      <div className="goals-list">
        <h3>Active Goals</h3>
        {goals.active.map(goal => (
          <div key={goal.goal_id} className="goal-item">
            <h4>{goal.title}</h4>
            <p>{goal.description}</p>
            <p>Target: ${goal.target_amount}</p>
            <p>Current: ${goal.current_amount || 0}</p>
            <p>Deadline: {new Date(goal.due_date).toLocaleDateString()}</p>
            <button onClick={() => handleDelete(goal.goal_id)}>Delete</button>
          </div>
        ))}

        <h3>Completed Goals</h3>
        {goals.completed.map(goal => (
          <div key={goal.goal_id} className="goal-item completed">
            <h4>{goal.title}</h4>
            <p>{goal.description}</p>
            <p>Target: ${goal.target_amount}</p>
            <p>Achieved: ${goal.current_amount || goal.target_amount}</p>
            <p>Completed on: {new Date(goal.due_date).toLocaleDateString()}</p>
            <button onClick={() => handleDelete(goal.goal_id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Goals;