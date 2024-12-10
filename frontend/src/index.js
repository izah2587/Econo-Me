import React from 'react';
import ReactDOM from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <Auth0Provider
        domain='dev-xgm0lup6iwjt0i8k.us.auth0.com'
        clientId='h6VQMvtBnAn3ApXwVjiWcQSsGSHdk5hl'
        authorizationParams={{
            redirect_uri: window.location.origin,
            audience: 'EKtYAN3Rd7RCVsNhoAPLCuZ0j9AbQoA1',
        }}
    >
        <App />
    </Auth0Provider>
);
