import React from 'react';

const Modal = ({ show, onClose, onConfirm, error }) => {
  if (!show) return null; // Do not render if `show` is false

  return (
    <div style={modalOverlayStyle}>
      <div style={modalContentStyle}>
        <h2>Daily Email Reminders</h2>
        <p>Would you like to receive daily email reminders to add your expenses?</p>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '1rem' }}>
          <button onClick={() => onConfirm('Yes')} style={buttonStyle}>
            Yes
          </button>
          <button onClick={() => onConfirm('No')} style={{ ...buttonStyle, backgroundColor: '#ccc', color: '#000' }}>
            No
          </button>
        </div>
        <button onClick={onClose} style={closeButtonStyle}>
          Close
        </button>
      </div>
    </div>
  );
};

// Styles for Modal
const modalOverlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100vw',
  height: '100vh',
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
};

const modalContentStyle = {
  background: '#fff',
  padding: '2rem',
  borderRadius: '10px',
  width: '90%',
  maxWidth: '400px',
  textAlign: 'center',
  boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
};

const buttonStyle = {
  padding: '0.5rem 1rem',
  fontSize: '1rem',
  border: 'none',
  borderRadius: '5px',
  backgroundColor: '#007bff',
  color: '#fff',
  cursor: 'pointer',
  transition: 'background-color 0.3s ease',
};

const closeButtonStyle = {
  ...buttonStyle,
  backgroundColor: '#f44336',
  color: '#fff',
};

export default Modal;
