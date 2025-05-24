// frontend/src/pages/PartDetailPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getPartByIdAPI, recyclePart as recyclePartAPI } from '../api/partService';

function PartDetailPage() {
    const { partId } = useParams(); // URL'den partId'yi al
    const { token, isAuthenticated, user } = useAuth();
    const navigate = useNavigate();

    const [part, setPart] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchPartDetail = useCallback(async () => {
        if (!token || !partId) return;
        setLoading(true);
        setError('');
        try {
            const data = await getPartByIdAPI(partId);
            setPart(data);
        } catch (err) {
            console.error("Parça detayı çekilirken hata:", err);
            setError(err.response?.data?.detail || "Parça detayı yüklenemedi.");
        } finally {
            setLoading(false);
        }
    }, [token, partId]);

    useEffect(() => {
        if (isAuthenticated) {
            fetchPartDetail();
        }
    }, [isAuthenticated, fetchPartDetail]);

    const handleRecycle = async () => {
        if (!part) return;
        if (window.confirm(`${part.serial_number} S/N'li parçayı geri dönüşüme göndermek istediğinize emin misiniz?`)) {
            setLoading(true);
            setError('');
            try {
                await recyclePartAPI(part.id);
                alert("Parça başarıyla geri dönüşüme gönderildi.");
                fetchPartDetail(); 
            } catch (err) {
                console.error("Parça geri dönüşüm hatası:", err);
                setError(err.response?.data?.error || err.response?.data?.detail || "Geri dönüşüm sırasında bir hata oluştu.");
            } finally {
                setLoading(false);
            }
        }
    };
    
    const canUserRecycle = user && part && user.profile?.team?.id === part.produced_by_team && part.status !== 'GERI_DONUSUMDE' && part.status !== 'KULLANILDI';


    if (loading) {
        return <div className="p-6 text-center text-gray-500">Parça detayları yükleniyor...</div>;
    }
    if (error) {
        return (
            <div className="container mx-auto p-4">
                <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 rounded" role="alert">
                    <p className="font-bold">Hata!</p>
                    <p>{error}</p>
                </div>
                <Link to="/parts" className="text-indigo-600 hover:text-indigo-800">Parça Listesine Geri Dön</Link>
            </div>
        );
    }
    if (!part) {
        return <div className="p-6 text-center text-gray-500">Parça bulunamadı.</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <div className="bg-white p-6 rounded-xl shadow-xl">
                <div className="flex justify-between items-center mb-6 pb-4 border-b">
                    <h1 className="text-3xl font-semibold text-gray-700">
                        Parça Detayı: <span className="text-indigo-600">{part.serial_number}</span>
                    </h1>
                    <Link to="/parts" className="text-sm text-indigo-600 hover:text-indigo-800">
                        ← Parça Listesine Dön
                    </Link>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                    <div><strong className="text-gray-600">ID:</strong> {part.id}</div>
                    <div><strong className="text-gray-600">Seri Numarası:</strong> {part.serial_number}</div>
                    <div><strong className="text-gray-600">Parça Tipi:</strong> {part.part_type_name}</div>
                    <div><strong className="text-gray-600">Uyumlu Model:</strong> {part.aircraft_model_compatibility_name || 'Belirtilmemiş'}</div>
                    <div><strong className="text-gray-600">Durum:</strong> <span className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${part.status === 'STOKTA' ? 'bg-green-100 text-green-800' : part.status === 'KULLANILDI' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>{part.status_display}</span></div>
                    <div><strong className="text-gray-600">Üreten Takım:</strong> {part.produced_by_team_name || 'Belirtilmemiş'}</div>
                    <div><strong className="text-gray-600">Kullanıldığı Uçak (Kuyruk No):</strong> {part.used_in_aircraft_tail_number || 'Kullanılmıyor'}</div>
                    <div><strong className="text-gray-600">Oluşturulma Tarihi:</strong> {new Date(part.created_at).toLocaleString('tr-TR')}</div>
                    <div><strong className="text-gray-600">Son Güncelleme:</strong> {new Date(part.updated_at).toLocaleString('tr-TR')}</div>
                </div>

                <div className="mt-8 pt-6 border-t">
                    {/* İzinlere ve parçanın durumuna göre butonlar */}
                    {canUserRecycle && (
                        <button
                            onClick={handleRecycle}
                            disabled={loading}
                            className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
                        >
                            {loading ? 'İşleniyor...' : 'Geri Dönüşüme Gönder'}
                        </button>
                    )}

                </div>
            </div>
        </div>
    );
}

export default PartDetailPage;