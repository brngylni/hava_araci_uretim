// frontend/src/pages/AssembledAircraftDetailPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axiosInstance from '../api/axiosInstance'; // Veya aircraftService kullanın

function AssembledAircraftDetailPage() {
    const { aircraftId } = useParams();
    const { token, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    const [aircraft, setAircraft] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchAircraftDetail = useCallback(async () => {
        if (!token || !aircraftId) return;
        setLoading(true);
        setError('');
        try {
            const response = await axiosInstance.get(`/api/v1/montaj/assembled-aircrafts/${aircraftId}/`, {
                headers: { Authorization: `Token ${token}` }
            });
            setAircraft(response.data);
        } catch (err) {
            console.error("Uçak detayı çekilirken hata:", err);
            setError(err.response?.data?.detail || "Uçak detayı yüklenemedi.");
        } finally {
            setLoading(false);
        }
    }, [token, aircraftId]);

    useEffect(() => {
        if (isAuthenticated) {
            fetchAircraftDetail();
        }
    }, [isAuthenticated, fetchAircraftDetail]);

    if (loading) {
        return <div className="p-6 text-center text-gray-500">Uçak detayları yükleniyor...</div>;
    }
    if (error) {
        return (
            <div className="container mx-auto p-4">
                <div className="alert-danger p-4 mb-4">Hata: {error}</div>
                <Link to="/assembled-aircrafts" className="text-indigo-600 hover:text-indigo-800">← Uçak Listesine Dön</Link>
            </div>
        );
    }
    if (!aircraft) {
        return <div className="p-6 text-center text-gray-500">Uçak bulunamadı.</div>;
    }

    const partInfo = (label, partDetails) => (
        partDetails ? (
            <div>
                <strong className="text-gray-600">{label}:</strong> {partDetails.serial_number} 
                <span className="text-xs text-gray-500"> ({partDetails.part_type_name} - Uyumlu: {partDetails.aircraft_model_compatibility_name})</span>
            </div>
        ) : <div><strong className="text-gray-600">{label}:</strong> Bilgi Yok</div>
    );

    return (
        <div className="container mx-auto p-4">
            <div className="bg-white p-6 rounded-xl shadow-xl">
                <div className="flex justify-between items-center mb-6 pb-4 border-b">
                    <h1 className="text-3xl font-semibold text-gray-700">
                        Uçak Detayı: <span className="text-indigo-600">{aircraft.tail_number}</span>
                    </h1>
                    <Link to="/assembled-aircrafts" className="text-sm text-indigo-600 hover:text-indigo-800">
                        ← Uçak Listesine Dön
                    </Link>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 mb-6">
                    <div><strong className="text-gray-600">Model:</strong> {aircraft.aircraft_model_details?.name}</div>
                    <div><strong className="text-gray-600">Kuyruk Numarası:</strong> {aircraft.tail_number}</div>
                    <div><strong className="text-gray-600">Montaj Tarihi:</strong> {new Date(aircraft.assembly_date).toLocaleDateString('tr-TR')}</div>
                    <div><strong className="text-gray-600">Montajı Yapan Takım:</strong> {aircraft.assembled_by_team_details?.get_name_display || 'Belirtilmemiş'}</div>
                </div>

                <h2 className="text-xl font-semibold text-gray-700 mb-3 mt-6 pt-4 border-t">Kullanılan Parçalar</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                    {partInfo("Kanat", aircraft.wing_details)}
                    {partInfo("Gövde", aircraft.fuselage_details)}
                    {partInfo("Kuyruk", aircraft.tail_details)}
                    {partInfo("Aviyonik", aircraft.avionics_details)}
                </div>
                
                <div className="mt-8 pt-6 border-t">
                    <Link to={`/assembled-aircrafts/${aircraftId}/edit`} className="text-sm text-indigo-600 hover:text-indigo-800">
                        🛠️ Düzenle
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default AssembledAircraftDetailPage;