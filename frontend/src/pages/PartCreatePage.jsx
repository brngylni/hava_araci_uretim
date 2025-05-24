import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axiosInstance from '../api/axiosInstance';

function PartCreatePage() {
    const { token, user } = useAuth();
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        serial_number: '',
        part_type: '',
        aircraft_model_compatibility: '',
    });
    const [partTypes, setPartTypes] = useState([]);
    const [aircraftModels, setAircraftModels] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Parça Tiplerini ve Uçak Modellerini API'den çek
    useEffect(() => {
        if (!token) return;

        const fetchData = async () => {
            setLoading(true);
            try {
                const [ptRes, amRes] = await Promise.all([
                    axiosInstance.get('/api/v1/envanter/part-types/'),
                    axiosInstance.get('/api/v1/envanter/aircraft-models/')
                ]);
                setPartTypes(ptRes.data.results || ptRes.data || []);
                setAircraftModels(amRes.data.results || amRes.data || []);
            } catch (err) {
                console.error("Dropdown verileri çekilirken hata:", err);
                setError("Form için gerekli veriler yüklenemedi.");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [token]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!formData.part_type || !formData.aircraft_model_compatibility || !formData.serial_number) {
            setError("Lütfen tüm zorunlu alanları doldurun.");
            setLoading(false);
            return;
        }

        const dataToSubmit = {
            serial_number: formData.serial_number,
            part_type: parseInt(formData.part_type, 10),
            aircraft_model_compatibility: parseInt(formData.aircraft_model_compatibility, 10),
        };

        try {
            await axiosInstance.post('/api/v1/envanter/parts/', dataToSubmit, {
                headers: { Authorization: `Token ${token}` }
            });
            alert('Parça başarıyla oluşturuldu!');
            navigate('/parts'); // Parça listesine geri dön
        } catch (err) {
            console.error("Parça oluşturma hatası:", err.response?.data || err.message);
            if (err.response && err.response.data) {
                // Hataları formatla
                let apiErrors = err.response.data;
                let errorMessages = [];
                for (const key in apiErrors) {
                    if (Array.isArray(apiErrors[key])) {
                        errorMessages.push(`${key}: ${apiErrors[key].join(', ')}`);
                    } else {
                        errorMessages.push(`${key}: ${apiErrors[key]}`);
                    }
                }
                setError(errorMessages.join('\n') || "Parça oluşturulamadı. Lütfen bilgileri kontrol edin.");
            } else {
                setError("Parça oluşturulurken bir hata oluştu.");
            }
        } finally {
            setLoading(false);
        }
    };
    
    const userTeam = user?.profile?.team_details; 
    const responsiblePartTypeId = user?.profile?.team?.responsible_part_type; 

    const availablePartTypes = partTypes.filter(pt => {
        if (!userTeam || userTeam.name === 'MONTAJ') return false; // Montaj takımı üretemez
        return true; 
    });


    if (loading && partTypes.length === 0) { // İlk yükleme
        return <div className="p-6 text-center">Form verileri yükleniyor...</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-semibold text-gray-700 mb-6">Yeni Parça Üret</h1>
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
                    <p className="font-bold">Hata!</p>
                    <pre className="whitespace-pre-wrap">{error}</pre>
                </div>
            )}
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-xl space-y-6">
                <div>
                    <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700 mb-1">
                        Seri Numarası <span className="text-red-500">*</span>
                    </label>
                    <input
                        type="text"
                        name="serial_number"
                        id="serial_number"
                        value={formData.serial_number}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                </div>

                <div>
                    <label htmlFor="part_type" className="block text-sm font-medium text-gray-700 mb-1">
                        Parça Tipi <span className="text-red-500">*</span>
                    </label>
                    <select
                        name="part_type"
                        id="part_type"
                        value={formData.part_type}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                        <option value="">Seçiniz...</option>
                        {partTypes.map(pt => (
                            <option key={pt.id} value={pt.id}>{pt.get_name_display}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label htmlFor="aircraft_model_compatibility" className="block text-sm font-medium text-gray-700 mb-1">
                        Uyumlu Uçak Modeli <span className="text-red-500">*</span>
                    </label>
                    <select
                        name="aircraft_model_compatibility"
                        id="aircraft_model_compatibility"
                        value={formData.aircraft_model_compatibility}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                        <option value="">Seçiniz...</option>
                        {aircraftModels.map(am => (
                            <option key={am.id} value={am.id}>{am.get_name_display}</option>
                        ))}
                    </select>
                </div>
                                <div className="flex justify-end">
                    <button
                        type="button"
                        onClick={() => navigate('/parts')}
                        disabled={loading}
                        className="mr-3 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        İptal
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {loading ? 'Kaydediliyor...' : 'Parçayı Üret'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default PartCreatePage;