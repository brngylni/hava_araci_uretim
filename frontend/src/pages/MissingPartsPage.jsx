import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { checkMissingPartsAPI } from '../api/aircraftService';
import axiosInstance from '../api/axiosInstance';

function MissingPartsPage() {
    const { token, isAuthenticated, loading: authLoading } = useAuth();

    const [aircraftModels, setAircraftModels] = useState([]);
    const [selectedModelName, setSelectedModelName] = useState(''); // Uçak modelinin 'name' (kod) değerini tutar
    const [checkResult, setCheckResult] = useState(null); // API'den dönen tüm yanıtı tutar
    const [loadingCheck, setLoadingCheck] = useState(false); // Kontrol işlemi için loading
    const [error, setError] = useState('');
    const [loadingModels, setLoadingModels] = useState(true); // Uçak modelleri yüklenirken

    // Uçak Modellerini API'den çek
    useEffect(() => {
        if (!token || !isAuthenticated) {
            setLoadingModels(false);
            return;
        }
        setLoadingModels(true);
        const fetchModels = async () => {
            try {
                const res = await axiosInstance.get('/api/v1/envanter/aircraft-models/');
                setAircraftModels(res.data.results || res.data || []);
                setError('');
            } catch (err) {
                console.error("Uçak modelleri çekilirken hata:", err);
                setError("Sistemdeki uçak modelleri yüklenemedi. Lütfen daha sonra tekrar deneyin.");
            } finally {
                setLoadingModels(false);
            }
        };
        fetchModels();
    }, [token, isAuthenticated]);

    const handleModelChange = (e) => {
        setSelectedModelName(e.target.value);
        setCheckResult(null); // Model değiştiğinde eski sonucu ve hatayı temizle
        setError('');
    };

    const handleCheckParts = async () => {
        if (!selectedModelName) {
            setError("Lütfen bir uçak modeli seçin.");
            return;
        }
        setLoadingCheck(true);
        setError('');
        setCheckResult(null);
        try {
            const data = await checkMissingPartsAPI(selectedModelName); // API çağrısı
            setCheckResult(data);
        } catch (err) {
            setError(err.message || "Eksik parça kontrolü sırasında bir hata oluştu.");
        } finally {
            setLoadingCheck(false);
        }
    };

    if (authLoading) {
        return <div className="p-6 text-center text-gray-500">Kimlik doğrulanıyor...</div>;
    }
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />; // Veya bir mesaj göster
    }


    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-semibold text-gray-700">Eksik Parça Kontrolü</h1>
                <Link to="/dashboard" className="text-sm text-indigo-600 hover:text-indigo-800">
                    ← Ana Panele Dön
                </Link>
            </div>
            
            <div className="bg-white p-6 md:p-8 rounded-xl shadow-xl max-w-2xl mx-auto">
                <p className="text-gray-600 mb-6">
                    Bir uçak modeli için üretimde gerekli olan temel parçaların (Kanat, Gövde, Kuyruk, Aviyonik)
                    mevcut stok durumunu kontrol edebilirsiniz.
                </p>
                
                <div className="mb-6">
                    <label htmlFor="aircraft_model_select_check" className="block text-sm font-medium text-gray-700 mb-1">
                        Uçak Modeli Seçin:
                    </label>
                    {loadingModels ? (
                        <div className="form-select mt-1 block w-full bg-gray-100 animate-pulse h-10 rounded-md"></div>
                    ) : aircraftModels.length > 0 ? (
                        <select
                            id="aircraft_model_select_check"
                            value={selectedModelName}
                            onChange={handleModelChange}
                            className="form-select mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                        >
                            <option value="">Bir model seçin...</option>
                            {aircraftModels.map(model => (
                                // MissingPartsQuerySerializer `name` (kod) bekliyordu
                                <option key={model.id} value={model.name}>{model.get_name_display}</option>
                            ))}
                        </select>
                    ) : (
                        <p className="text-sm text-gray-500 mt-1">Yüklenecek uçak modeli bulunamadı.</p>
                    )}
                </div>

                <button
                    onClick={handleCheckParts}
                    disabled={!selectedModelName || loadingCheck || loadingModels}
                    className="btn-primary w-full disabled:opacity-60"
                >
                    {loadingCheck ? 'Kontrol Ediliyor...' : 'Eksik Parçaları Kontrol Et'}
                </button>

                {error && (
                    <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
                        <div className="flex">
                            <div className="flex-shrink-0">
                                {/* Hata ikonu eklenebilir */}
                            </div>
                            <div className="ml-3">
                                <p className="text-sm font-medium text-red-800">Bir Hata Oluştu</p>
                                <p className="mt-1 text-sm text-red-700">{error}</p>
                            </div>
                        </div>
                    </div>
                )}

                {checkResult && !error && ( // Sadece sonuç varsa ve hata yoksa göster
                    <div className="mt-8 p-4 border border-gray-200 rounded-md bg-gray-50">
                        <h2 className="text-xl font-semibold text-gray-800 mb-3">
                            Kontrol Sonuçları: <span className="text-indigo-600">{checkResult.aircraft_model}</span>
                        </h2>
                        
                        {checkResult.message && (!checkResult.warnings || checkResult.warnings.length === 0) && (
                            <div className="bg-green-50 border-l-4 border-green-400 p-3 mb-4 rounded-md">
                                <p className="text-sm font-medium text-green-700">{checkResult.message}</p>
                            </div>
                        )}

                        {checkResult.warnings && checkResult.warnings.length > 0 && (
                            <div className="mb-4 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-md">
                                <h3 className="text-sm font-medium text-yellow-800 mb-1">Uyarılar:</h3>
                                <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                                    {checkResult.warnings.map((warning, index) => (
                                        <li key={index}>{warning}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        
                        <h3 className="text-md font-medium text-gray-700 mt-4 mb-2">Mevcut Parça Sayıları:</h3>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-100">
                                    <tr>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Parça Tipi</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stok Adedi</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {Object.entries(checkResult.required_parts_check).map(([partName, count]) => (
                                        <tr key={partName} className={count === 0 ? "bg-red-50" : ""}>
                                            <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{partName}</td>
                                            <td className={`px-4 py-2 whitespace-nowrap text-sm ${count === 0 ? "text-red-600 font-semibold" : "text-gray-700"}`}>{count} adet</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default MissingPartsPage;