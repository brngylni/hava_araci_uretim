import React, { createContext, useState, useEffect, useContext } from 'react';
import axiosInstance from '../api/axiosInstance';
import { loginUser as apiLogin, fetchCurrentUser as apiFetchCurrentUser } from '../api/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('authToken'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadUserFromToken = async () => {
            if (token) {
                axiosInstance.defaults.headers.common['Authorization'] = `Token ${token}`;
                try {
                    const userData = await apiFetchCurrentUser();
                    setUser(userData);
                } catch (error) {
                    console.error("Failed to fetch user with token, logging out:", error);
                    localStorage.removeItem('authToken');
                    setToken(null);
                    setUser(null);
                    delete axiosInstance.defaults.headers.common['Authorization'];
                }
            }
            setLoading(false);
        };
        loadUserFromToken();
    }, [token]);

    const login = async (username, password) => {
        const data = await apiLogin(username, password); // Servis fonksiyonunu kullan
        const { token: newToken, user: userData } = data;
        localStorage.setItem('authToken', newToken);
        setToken(newToken); // Bu, yukarıdaki useEffect'i tetikleyerek user'ı günceller
        setUser(userData); 
        return true;
    };

    const logout = () => {
        localStorage.removeItem('authToken');
        setToken(null);
        setUser(null);
        delete axiosInstance.defaults.headers.common['Authorization'];
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, loading, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};