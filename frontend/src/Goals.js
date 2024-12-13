import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth0 } from '@auth0/auth0-react';
import Confetti from 'react-confetti'; // Import the confetti library
import './Goals.css';

const Goals = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [goals, setGoals] = useState({ active: [], completed: [] });
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    target_amount: '',
    current_amount: '',
    deadline: '',
  });
  const [editGoal, setEditGoal] = useState(null);  
  const [error, setError] = useState(null);
  const [showConfetti, setShowConfetti] = useState(false); // State for confetti animation

  const fetchGoals = async () => {
    try {
      const token = await getAccessTokenSilently();
      const response = await axios.get(`https://econome-backend-102803836636.us-central1.run.app/goals`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Cache-Control": "no-cache",
        },
      });
  
      const allGoals = response.data.goals;
      setGoals({
        active: allGoals.filter((goal) => goal.status === "active"),
        completed: allGoals.filter((goal) => goal.status === "completed"),
      });
      console.log("Completed goals:", goals.completed);
    } catch (error) {
      console.error("Error fetching goals:", error);
      setError("Failed to fetch goals. Please try again later.");
    }
  };
  

  useEffect(() => {
    console.log("Fetching goals...");
    fetchGoals();
  }, [getAccessTokenSilently]);
  
  const handleInputChange = (e) => {
    setNewGoal({ ...newGoal, [e.target.name]: e.target.value });
  };

  const handleEditInputChange = (e) => {
    const updatedField = { [e.target.name]: e.target.value };
    console.log("Updating field:", updatedField);
    const updatedGoal = { ...editGoal, ...updatedField };
    setEditGoal(updatedGoal);
    console.log("Updated editGoal state:", updatedGoal);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = await getAccessTokenSilently();
      const goalData = {
        title: newGoal.title,
        description: newGoal.description,
        target_amount: parseFloat(newGoal.target_amount),
        current_amount: parseFloat(newGoal.current_amount),
        deadline: newGoal.deadline,
      };
      console.log('Sending goal data:', goalData);
      await axios.post(`https://econome-backend-102803836636.us-central1.run.app/goals`, goalData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      setNewGoal({ title: '', description: '', target_amount: '', current_amount: '', deadline: '' });
      fetchGoals();
    } catch (error) {
      console.error('Error creating goal:', error);
      setError('Failed to create goal. Please try again.');
    }
  };

  const handleDelete = async (goalId) => {
    try {
      const token = await getAccessTokenSilently();
      await axios.delete(`https://econome-backend-102803836636.us-central1.run.app/goals/${goalId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchGoals();
    } catch (error) {
      console.error('Error deleting goal:', error);
      setError('Failed to delete goal. Please try again.');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = await getAccessTokenSilently();
      const updatedFields = {
        title: editGoal.title || "",
        description: editGoal.description || "",
        target_amount: parseFloat(editGoal.target_amount) || 0,
        current_amount: parseFloat(editGoal.current_amount),
        due_date: editGoal.deadline || "",
      };
  
      console.log("Updating goal data:", updatedFields);
      
      await axios.put(
        `https://econome-backend-102803836636.us-central1.run.app/goals/${editGoal.goal_id}`,
        updatedFields,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
  
      // Check if the goal is completed
      if (updatedFields.current_amount === updatedFields.target_amount) {
        setShowConfetti(true); // Trigger confetti animation
        setTimeout(() => setShowConfetti(false), 5000); // Stop confetti after 5 seconds
      }

      fetchGoals(); // Refresh goals
      setEditGoal(null); // Clear edit state after refresh

    } catch (error) {
      console.error("Error updating goal:", error);
      setError("Failed to update goal. Please try again.");
    }
  };
  
  return (
    <div className="goals-container">
      {showConfetti && <Confetti />} {/* Confetti animation */}
      {error && <div className="error">{error}</div>}
      <h3>Set New Goal</h3>
  
      <form onSubmit={handleSubmit} className="new-goal-form">
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
          type="number"
          name="current_amount"
          value={newGoal.current_amount}
          onChange={handleInputChange}
          placeholder="Current Amount"
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
  
      <div key={JSON.stringify(goals.active)} className="goals-list">
        <h3>Active Goals</h3>
        {goals.active.map((goal) => (
          <div key={goal.goal_id} className="goal-item">
            <h4>{goal.title}</h4>
            <p>{goal.description}</p>
            <p>Target: ${goal.target_amount}</p>
            <p>Current: ${goal.current_amount}</p>
            <p>Deadline: {new Date(goal.due_date).toLocaleDateString()}</p>
            <button onClick={() => handleDelete(goal.goal_id)}>Delete</button>
            <button
              onClick={() =>
                setEditGoal({
                  ...goal,
                  target_amount: goal.target_amount || '',
                  current_amount: goal.current_amount || '',
                  title: goal.title || '',
                  description: goal.description || '',
                  deadline: goal.due_date || '',
                })
              }
            >
              Edit
            </button>
          </div>
        ))}
        {editGoal && (
          <form onSubmit={handleEditSubmit} className="edit-goal-form">
            <h3>Edit Goal</h3>
            <input
              type="text"
              name="title"
              value={editGoal.title || ""}
              onChange={handleEditInputChange}
              placeholder="Goal Title"
            />
            <textarea
              name="description"
              value={editGoal.description || ""}
              onChange={handleEditInputChange}
              placeholder="Goal Description"
            />
            <input
              type="number"
              name="target_amount"
              value={editGoal.target_amount || ""}
              onChange={handleEditInputChange}
              placeholder="Target Amount"
            />
            <input
              type="number"
              name="current_amount"
              value={editGoal.current_amount || ""}
              onChange={handleEditInputChange}
              placeholder="Current Amount"
            />
            <input
              type="date"
              name="deadline"
              value={editGoal.deadline || ""}
              onChange={handleEditInputChange}
            />
            <button type="submit">Update Goal</button>
            <button type="button" onClick={() => setEditGoal(null)}>
              Cancel
            </button>
          </form>
        )}
  
        <h3>Completed Goals</h3>
        {console.log("Completed goals:", goals.completed)} {/* Debug log */}
        {goals.completed.map((goal) => (
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
