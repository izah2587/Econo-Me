import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth0 } from '@auth0/auth0-react';

const Profile = () => {
    const { getAccessTokenSilently } = useAuth0();
    const [profile, setProfile] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const token = await getAccessTokenSilently();
                const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/profile`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setProfile(response.data.user);
                setError(null);
            } catch (error) {
                console.error("Error fetching profile:", error);
                setError("Failed to fetch profile. Please try again later.");
                setProfile(null);
            }
        };

        fetchProfile();
    }, [getAccessTokenSilently]);

    if (error) {
        return <div className="error">{error}</div>;
    }

    if (!profile) {
        return <div>Loading...</div>;
    }

    return (
        <div className="profile">
            <h2>Profile</h2>
            <p><strong>ID:</strong> {profile.id}</p>
            <p><strong>Auth0 ID:</strong> {profile.auth0_id}</p>
            <p><strong>Name:</strong> {profile.name}</p>
            <p><strong>Email:</strong> {profile.email}</p>
        </div>
    );
};

export default Profile;