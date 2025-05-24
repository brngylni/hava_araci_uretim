import React, { useState, useEffect } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { registerUser } from '../api/authService'; 
import { useAuth } from '../contexts/AuthContext';

function RegisterPage() {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        password2: '',
        first_name: '',
        last_name: '',
        team_id: '', // Opsiyonel takım ID'si
    });
    const [teams, setTeams] = useState([]);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    useEffect(() => {
      
    }, []);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccessMessage('');
        if (formData.password !== formData.password2) {
            setError('Şifreler eşleşmiyor.');
            return;
        }

        try {
            const dataToSubmit = { ...formData };
            if (!dataToSubmit.team_id) { // Eğer team_id boşsa veya seçilmemişse null gönder
                dataToSubmit.team_id = null;
            } else {
                dataToSubmit.team_id = parseInt(dataToSubmit.team_id, 10); // Integer'a çevir
            }

            await registerUser(dataToSubmit);
            setSuccessMessage('Kayıt başarılı! Lütfen giriş yapın.');
            setTimeout(() => {
                navigate('/login');
            }, 2000); // 2 saniye sonra login sayfasına yönlendir
        } catch (err) {
            if (err.response && err.response.data) {
                // Hataları formatlayarak göster
                let errorMessage = '';
                for (const key in err.response.data) {
                    errorMessage += `${key}: ${err.response.data[key].join ? err.response.data[key].join(', ') : err.response.data[key]}\n`;
                }
                setError(errorMessage.trim() || 'Kayıt başarısız. Lütfen bilgilerinizi kontrol edin.');
            } else {
                setError('Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.');
            }
            console.error("Registration page error:", err);
        }
    };

    if (isAuthenticated) {
        return <Navigate to="/dashboard" replace />; // Zaten giriş yapmışsa dashboard'a yönlendir
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Yeni Hesap Oluştur
                    </h2>
                </div>
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                        <strong className="font-bold">Hata!</strong>
                        <span className="block sm:inline"> {error.split('\n').map((line, i) => (<React.Fragment key={i}>{line}<br/></React.Fragment>))}</span>
                    </div>
                )}
                {successMessage && (
                    <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                        <strong className="font-bold">Başarılı!</strong>
                        <span className="block sm:inline"> {successMessage}</span>
                    </div>
                )}
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label htmlFor="username" className="sr-only">Kullanıcı Adı</label>
                            <input id="username" name="username" type="text" required value={formData.username} onChange={handleChange}
                                   className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                   placeholder="Kullanıcı Adı"/>
                        </div>
                        <div>
                            <label htmlFor="email" className="sr-only">E-posta Adresi</label>
                            <input id="email" name="email" type="email" autoComplete="email" required value={formData.email} onChange={handleChange}
                                   className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                   placeholder="E-posta Adresi"/>
                        </div>
                        <div>
                            <label htmlFor="first_name" className="sr-only">Ad</label>
                            <input id="first_name" name="first_name" type="text" value={formData.first_name} onChange={handleChange}
                                   className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                   placeholder="Ad (İsteğe Bağlı)"/>
                        </div>
                        <div>
                            <label htmlFor="last_name" className="sr-only">Soyad</label>
                            <input id="last_name" name="last_name" type="text" value={formData.last_name} onChange={handleChange}
                                   className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                   placeholder="Soyad (İsteğe Bağlı)"/>
                        </div>
                        <div>
                            <label htmlFor="password_reg" className="sr-only">Şifre</label> 
                            <input id="password_reg" name="password" type="password" required value={formData.password} onChange={handleChange}
                                   className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                   placeholder="Şifre"/>
                        </div>
                        <div>
                            <label htmlFor="password2_reg" className="sr-only">Şifre Tekrar</label>
                            <input id="password2_reg" name="password2" type="password" required value={formData.password2} onChange={handleChange}
                                   className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                   placeholder="Şifre Tekrar"/>
                        </div>
                    </div>

                    {teams.length > 0 && (
                        <div className="mt-4">
                            <label htmlFor="team_id" className="block text-sm font-medium text-gray-700">
                                Takım (İsteğe Bağlı)
                            </label>
                            <select id="team_id" name="team_id" value={formData.team_id} onChange={handleChange}
                                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
                                <option value="">Takım Seçmeyin</option>
                                {teams.map(team => (
                                    <option key={team.id} value={team.id}>{team.get_name_display}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    <div>
                        <button type="submit"
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Kayıt Ol
                        </button>
                    </div>
                </form>
                <div className="mt-6">
                    <p className="text-center text-sm text-gray-600">
                        Zaten bir hesabınız var mı?{' '}
                        <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                            Giriş yapın
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default RegisterPage;