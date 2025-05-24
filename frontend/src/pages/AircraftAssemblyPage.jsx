import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axiosInstance from '../api/axiosInstance';


const PART_FIELD_DEFINITIONS = [
    { fieldKey: 'wing', typeCode: 'KANAT', label: 'Kanat' },
    { fieldKey: 'fuselage', typeCode: 'GOVDE', label: 'Gövde' },
    { fieldKey: 'tail', typeCode: 'KUYRUK', label: 'Kuyruk' },
    { fieldKey: 'avionics', typeCode: 'AVIYONIK', label: 'Aviyonik' },
];

function AircraftAssemblyPage() {
    const { token, user, isAuthenticated, loading: authLoading } = useAuth();
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        tail_number: '',
        aircraft_model: '',
        wing: '', fuselage: '', tail: '', avionics: ''
    });
    const [aircraftModels, setAircraftModels] = useState([]);
    const [partTypeMap, setPartTypeMap] = useState({});
    
    const [availableParts, setAvailableParts] = useState({
        wing: [], fuselage: [], tail: [], avionics: []
    });

    const [error, setError] = useState('');
    const [loadingFormSubmit, setLoadingFormSubmit] = useState(false);
    const [loadingDropdownData, setLoadingDropdownData] = useState(true);

    useEffect(() => {
        if (!token || !isAuthenticated) { // Sadece giriş yapılmışsa ve token varsa
             setLoadingDropdownData(false); // Eğer token yoksa yüklemeyi bitir
            return;
        }
        setLoadingDropdownData(true);
        const fetchInitialData = async () => {
            try {
                const [amRes, ptRes] = await Promise.all([
                    axiosInstance.get('/api/v1/envanter/aircraft-models/'),
                    axiosInstance.get('/api/v1/envanter/part-types/')
                ]);
                setAircraftModels(amRes.data.results || amRes.data || []);
                
                const ptMap = {};
                (ptRes.data.results || ptRes.data || []).forEach(pt => {
                    ptMap[pt.name] = pt.id;
                });
                setPartTypeMap(ptMap);
                setError('');
            } catch (err) {
                console.error("Dropdown verileri çekilirken hata:", err);
                setError("Form için temel veriler yüklenemedi.");
            } finally {
                setLoadingDropdownData(false);
            }
        };
        fetchInitialData();
    }, [token, isAuthenticated]);

    const fetchPartsForSpecificType = useCallback(async (aircraftModelId, partTypeCode) => {
        if (!token || !aircraftModelId || !partTypeCode || !partTypeMap[partTypeCode]) {
            if (aircraftModelId && partTypeCode && Object.keys(partTypeMap).length > 0 && !partTypeMap[partTypeCode]) {
                 console.warn(`fetchPartsForSpecificType: PartType ID for code '${partTypeCode}' not found in partTypeMap. Map:`, partTypeMap);
            }
            return [];
        }
        
        const partTypeId = partTypeMap[partTypeCode];

        try {
            const apiUrl = `/api/v1/envanter/parts/?status=STOKTA&aircraft_model_compatibility=${aircraftModelId}&part_type=${partTypeId}`;
            const res = await axiosInstance.get(apiUrl);
            return res.data.results || res.data || [];
        } catch (err) {
            console.error(`${partTypeCode} için parçalar çekilirken hata:`, err.response?.data || err.message);
            return [];
        }
    }, [token, partTypeMap]);

    useEffect(() => {
        if (formData.aircraft_model && Object.keys(partTypeMap).length > 0 && isAuthenticated) { // isAuthenticated kontrolü
            setLoadingDropdownData(true);
            
            const fetchAllPartOptions = async () => {
                // Promise.all ile paralel istekler
                const results = await Promise.all(
                    PART_FIELD_DEFINITIONS.map(def => 
                        fetchPartsForSpecificType(formData.aircraft_model, def.typeCode)
                    )
                );
                setAvailableParts({
                    wing: results[0] || [],
                    fuselage: results[1] || [],
                    tail: results[2] || [],
                    avionics: results[3] || [],
                });
                setLoadingDropdownData(false);
            };
            fetchAllPartOptions().catch(err => { // Promise.all'dan gelebilecek genel hata
                console.error("Parça listeleri çekilirken toplu hata:", err);
                setError("Parça seçenekleri yüklenirken bir sorun oluştu.");
                setLoadingDropdownData(false);
            });

        } else {
            setAvailableParts({ wing: [], fuselage: [], tail: [], avionics: [] });
            if (!formData.aircraft_model) {
                setLoadingDropdownData(false);
            }
        }
    }, [formData.aircraft_model, partTypeMap, fetchPartsForSpecificType, isAuthenticated]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (name === 'aircraft_model') {
            setFormData(prev => ({
                ...prev,
                wing: '', fuselage: '', tail: '', avionics: '',
                aircraft_model: value
            }));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoadingFormSubmit(true); 

        const { tail_number, aircraft_model, wing, fuselage, tail, avionics } = formData;
        if (!tail_number || !aircraft_model || !wing || !fuselage || !tail || !avionics) {
            setError("Lütfen tüm zorunlu alanları doldurun.");
            setLoadingFormSubmit(false);
            return;
        }
        const dataToSubmit = {
            tail_number,
            aircraft_model: parseInt(aircraft_model),
            wing: parseInt(wing),
            fuselage: parseInt(fuselage),
            tail: parseInt(tail),
            avionics: parseInt(avionics),
        };

        try {
            await axiosInstance.post('/api/v1/montaj/assembled-aircrafts/', dataToSubmit); 
            alert('Uçak başarıyla monte edildi!');
            navigate('/assembled-aircrafts'); 
        } catch (err) {
            console.error("Uçak montaj hatası:", err.response?.data || err.message);
            if (err.response && err.response.data) {
                let apiErrors = err.response.data;
                let errorMessages = [];
                 Object.keys(apiErrors).forEach(key => {
                    const messages = Array.isArray(apiErrors[key]) ? apiErrors[key].join(', ') : apiErrors[key];
                    errorMessages.push(`${key === 'non_field_errors' ? 'Genel Hata' : key}: ${messages}`);
                });
                setError(errorMessages.join('\n') || "Montaj başarısız. Lütfen bilgileri kontrol edin.");
            } else {
                setError("Montaj sırasında bir hata oluştu.");
            }
        } finally {
            setLoadingFormSubmit(false);
        }
    };
    
    // Auth yüklenirken veya ilk dropdown verileri yüklenirken genel bir yükleme mesajı
    if (authLoading || (loadingDropdownData && (!aircraftModels.length || !Object.keys(partTypeMap).length))) {
        return <div className="p-6 text-center text-gray-500">Form için temel veriler yükleniyor...</div>;
    }
    if (!isAuthenticated) { // Giriş yapılmamışsa
        return <Navigate to="/login" replace />; // Login'e yönlendir
    }
    // Montaj takımı değilse erişimi engelle
    if (user && user.profile?.team_details?.get_name_display !== 'Montaj Takımı') {
         return <div className="p-6 text-center text-red-500">Bu sayfaya erişim yetkiniz yok.</div>;
    }


    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-semibold text-gray-700 mb-6">Yeni Uçak Monte Et</h1>
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
                    <p className="font-bold">Hata!</p>
                    <pre className="whitespace-pre-wrap text-sm">{error}</pre>
                </div>
            )}
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-xl space-y-6">
                <div>
                    <label htmlFor="tail_number" className="block text-sm font-medium text-gray-700 mb-1">Kuyruk Numarası <span className="text-red-500">*</span></label>
                    <input type="text" name="tail_number" id="tail_number" value={formData.tail_number} onChange={handleChange} required className="form-input mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                </div>
                <div>
                    <label htmlFor="aircraft_model" className="block text-sm font-medium text-gray-700 mb-1">Uçak Modeli <span className="text-red-500">*</span></label>
                    <select name="aircraft_model" id="aircraft_model" value={formData.aircraft_model} onChange={handleChange} required className="form-select mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
                        <option value="">Model Seçiniz...</option>
                        {aircraftModels.map(am => <option key={am.id} value={am.id}>{am.get_name_display}</option>)}
                    </select>
                </div>

                {PART_FIELD_DEFINITIONS.map(partDef => (
                    <div key={partDef.fieldKey}>
                        <label htmlFor={partDef.fieldKey} className="block text-sm font-medium text-gray-700 mb-1">
                            {partDef.label} <span className="text-red-500">*</span>
                        </label>
                        <select
                            name={partDef.fieldKey}
                            id={partDef.fieldKey}
                            value={formData[partDef.fieldKey]}
                            onChange={handleChange}
                            required
                            disabled={!formData.aircraft_model || loadingDropdownData}
                            className="form-select mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md disabled:bg-gray-100"
                        >
                            <option value="">
                                {loadingDropdownData && formData.aircraft_model ? 'Yükleniyor...' : (formData.aircraft_model ? `${partDef.label} Seçiniz...` : 'Önce Uçak Modeli Seçin')}
                            </option>
                            {(availableParts[partDef.fieldKey] || []).map(p => (
                                <option key={p.id} value={p.id}>
                                    {p.serial_number} ({p.part_type_name} - Uyumlu: {p.aircraft_model_compatibility_name})
                                </option>
                            ))}
                        </select>
                         {formData.aircraft_model && (availableParts[partDef.fieldKey] || []).length === 0 && !loadingDropdownData && (
                            <p className="text-xs text-red-500 mt-1">Bu model için uygun {partDef.label.toLowerCase()} bulunamadı veya stokta yok.</p>
                        )}
                    </div>
                ))}
                
                <div className="flex justify-end pt-4">
                    <button type="button" onClick={() => navigate(-1)} disabled={loadingFormSubmit} className="mr-3 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">İptal</button>
                    <button type="submit" disabled={loadingFormSubmit || loadingDropdownData} className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
                        {loadingFormSubmit ? 'Monte Ediliyor...' : 'Uçağı Monte Et'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default AircraftAssemblyPage;