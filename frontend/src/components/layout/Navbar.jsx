import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function Navbar() {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="bg-gray-800 text-white p-4 shadow-md">
            <div className="container mx-auto flex justify-between items-center">
                <Link to="/dashboard" className="text-xl font-bold hover:text-gray-300">
                    Hava Aracı Üretim Sistemi
                </Link>
                <div>
                    {isAuthenticated && user ? (
                        <>
                            <span className="mr-4">Merhaba, {user.first_name || user.username}!</span>
                            <button
                                onClick={handleLogout}
                                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                            >
                                Çıkış Yap
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="mr-4 hover:text-gray-300">Giriş Yap</Link>
                            <Link to="/register" className="hover:text-gray-300">Kayıt Ol</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}

export default Navbar;