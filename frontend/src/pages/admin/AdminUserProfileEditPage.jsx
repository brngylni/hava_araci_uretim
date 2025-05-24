import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getUserProfileByIdAPI, updateUserProfileAPI } from '../../api/userService'; 
import axiosInstance from '../../api/axiosInstance'; 

function AdminUserProfileEditPage() {
    const { userId } = useParams(); 
    const { token } = useAuth();
    const navigate = useNavigate();

    const [profileData, setProfileData] = useState(null); // User.profile objesi
    const [selectedTeamId, setSelectedTeamId] = useState('');
    const [teams, setTeams] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);
    const [username, setUsername] = useState(''); // Sadece göstermek için

    // Takım listesini ve mevcut profil verisini çek
    useEffect(() => {
        if (!token || !userId) return;
        setLoading(true);

        const fetchInitialData = async () => {
            try {
                // Önce User objesini çekip içinden profile ID'sini alalım
                const userRes = await axiosInstance.get(`/api/v1/users/users/${userId}/`, {
                    headers: { Authorization: `Token ${token}` }
                });
                const userDetail = userRes.data;
                setUsername(userDetail.username);

                if (userDetail.profile && userDetail.profile.id) {
                    const profileId = userDetail.profile.id;
                    const [currentProfileRes, teamsRes] = await Promise.all([
                        getUserProfileByIdAPI(profileId), // Artık profileId ile çekiyoruz
                        axiosInstance.get('/api/v1/uretim/teams/') // Takım listesi
                    ]);
                    setProfileData(currentProfileRes);
                    setSelectedTeamId(currentProfileRes.team || ''); // Mevcut takım ID'si veya boş
                    setTeams(teamsRes.data.results || teamsRes.data || []);
                } else {
                    throw new Error("Kullanıcı için profil bilgisi bulunamadı.");
                }
                setError('');
            } catch (err) {
                console.error("Profil düzenleme için veri çekilirken hata:", err);
                setError("Veriler yüklenemedi: " + (err.message || "Bilinmeyen hata"));
                setProfileData(null); // Hata durumunda formu gösterme
            } finally {
                setLoading(false);
            }
        };
        fetchInitialData();
    }, [token, userId]);

    const handleTeamChange = (e) => {
        setSelectedTeamId(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!profileData) {
            setError("Profil verisi yüklenemedi, kayıt yapılamaz.");
            return;
        }
        setError('');
        setLoading(true);

        const dataToSubmit = {
            team: selectedTeamId ? parseInt(selectedTeamId, 10) : null, // null veya geçerli bir ID
        };

        try {
            await updateUserProfileAPI(profileData.id, dataToSubmit);
            alert('Kullanıcı profili başarıyla güncellendi!');
            navigate('/admin/users'); // Kullanıcı listesine geri dön
        } catch (err) {
            console.error("Profil güncelleme hatası:", err.response?.data || err.message);
            if (err.response && err.response.data) {
                let apiErrors = err.response.data;
                let errorMessages = [];
                Object.keys(apiErrors).forEach(key => {
                    const messages = Array.isArray(apiErrors[key]) ? apiErrors[key].join(', ') : apiErrors[key];
                    errorMessages.push(`${key === 'non_field_errors' ? 'Genel Hata' : key}: ${messages}`);
                });
                setError(errorMessages.join('\n') || "Profil güncellenemedi.");
            } else {
                setError("Profil güncellenirken bir hata oluştu.");
            }
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="p-6 text-center">Kullanıcı profil bilgileri yükleniyor...</div>;
    }
    if (error && !profileData) { // İlk yüklemede kritik hata varsa
        return <div className="alert-danger p-4">Hata: {error} <Link to="/admin/users" className="underline">Kullanıcı Listesine Dön</Link></div>;
    }
    if (!profileData) { // Profil bulunamadıysa (yukarıdaki error bunu yakalamalı ama defensive)
        return <div className="p-6 text-center text-gray-500">Kullanıcı profili bulunamadı.</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-semibold text-gray-700 mb-6">
                Kullanıcı Profilini Düzenle: <span className="text-indigo-600">{username}</span>
            </h1>
            {error && <div className="alert-danger mb-4"><pre>{error}</pre></div>}
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-xl space-y-6">
                <p className="text-sm text-gray-600">Kullanıcı: {username} (ID: {userId})</p>
                <p className="text-sm text-gray-600">Profil ID: {profileData.id}</p>
                
                <div>
                    <label htmlFor="team" className="form-label">Takımı</label>
                    <select
                        name="team"
                        id="team"
                        value={selectedTeamId}
                        onChange={handleTeamChange}
                        className="form-select"
                    >
                        <option value="">Takımsız</option>
                        {teams.map(team => (
                            <option key={team.id} value={team.id}>{team.get_name_display}</option>
                        ))}
                    </select>
                </div>
                {/* UserProfile'a başka düzenlenebilir alanlar eklenirse buraya form elemanları gelir */}
                
                <div className="flex justify-end pt-4">
                    <button type="button" onClick={() => navigate('/admin/users')} disabled={loading} className="btn-secondary mr-3">İptal</button>
                    <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50">
                        {loading ? 'Kaydediliyor...' : 'Profili Güncelle'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default AdminUserProfileEditPage;