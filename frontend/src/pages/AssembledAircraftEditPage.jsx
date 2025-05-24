import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getAssembledAircraftByIdAPI, updateAssembledAircraftAPI } from '../api/aircraftService';
import axiosInstance from '../api/axiosInstance';

// Parça alanları ve beklenen tipleri için sabit (AircraftAssemblyPage'deki gibi)
const PART_FIELD_DEFINITIONS = [
    { fieldKey: 'wing', typeCode: 'KANAT', label: 'Kanat' },
    { fieldKey: 'fuselage', typeCode: 'GOVDE', label: 'Gövde' },
    { fieldKey: 'tail', typeCode: 'KUYRUK', label: 'Kuyruk' },
    { fieldKey: 'avionics', typeCode: 'AVIYONIK', label: 'Aviyonik' },
];

/**
 * Monte edilmiş bir uçağın bilgilerini (kuyruk numarası ve parçaları)
 * düzenlemek için kullanılan sayfa bileşeni.
 * Sadece Montaj Takımı üyeleri erişebilir (backend izni ile).
 */
function AssembledAircraftEditPage() {
    const { aircraftId } = useParams(); // URL'den düzenlenecek uçağın ID'si
    const { token, user, isAuthenticated, loading: authLoading } = useAuth();
    const navigate = useNavigate();

    // Form verileri state'i (başlangıçta boş)
    const [formData, setFormData] = useState({
        tail_number: '',
        wing: '', fuselage: '', tail: '', avionics: ''
    });
    const [originalAircraft, setOriginalAircraft] = useState(null); // Uçağın orijinal verilerini tutar
    const [partTypeMap, setPartTypeMap] = useState({}); // { 'KANAT': id, ... }
    
    // Her parça tipi için dropdown seçeneklerini tutan state
    const [availableParts, setAvailableParts] = useState({
        wing: [], fuselage: [], tail: [], avionics: []
    });

    const [error, setError] = useState('');
    const [loadingPage, setLoadingPage] = useState(true); // Sayfa ilk yüklenirken genel loading
    const [loadingPartOptions, setLoadingPartOptions] = useState(false); // Parça seçenekleri yüklenirken
    const [submittingForm, setSubmittingForm] = useState(false); // Form submit edilirken

    // Parça tipi kodu ve uçak model ID'sine göre stoktaki uyumlu parçaları çek
    const fetchPartsForSpecificType = useCallback(async (targetAircraftModelId, partTypeCode) => {
        if (!token || !targetAircraftModelId || !partTypeCode || !partTypeMap[partTypeCode]) {
            return [];
        }
        const partTypeId = partTypeMap[partTypeCode];
        try {
            const apiUrl = `/api/v1/envanter/parts/?status=STOKTA&aircraft_model_compatibility=${targetAircraftModelId}&part_type=${partTypeId}`;
            const res = await axiosInstance.get(apiUrl);
            return res.data.results || res.data || [];
        } catch (err) {
            console.error(`${partTypeCode} için parçalar çekilirken hata:`, err.response?.data || err.message);
            return [];
        }
    }, [token, partTypeMap]);

    // Component mount olduğunda ve aircraftId değiştiğinde uçağın mevcut verilerini çek
    useEffect(() => {
        if (!token || !aircraftId || !isAuthenticated) { // Auth kontrolü
            if (!authLoading && !isAuthenticated) navigate("/login"); // Auth yoksa login'e
            return;
        }
        setLoadingPage(true);
        const fetchInitialAircraftData = async () => {
            try {
                const currentAircraftData = await getAssembledAircraftByIdAPI(aircraftId);
                setOriginalAircraft(currentAircraftData);
                setFormData({
                    tail_number: currentAircraftData.tail_number,
                    wing: currentAircraftData.wing || '', // Mevcut parça ID'leri
                    fuselage: currentAircraftData.fuselage || '',
                    tail: currentAircraftData.tail || '',
                    avionics: currentAircraftData.avionics || '',
                });

                const ptRes = await axiosInstance.get('/api/v1/envanter/part-types/');
                const ptMap = {};
                (ptRes.data.results || ptRes.data || []).forEach(pt => { ptMap[pt.name] = pt.id; });
                setPartTypeMap(ptMap);
                setError('');
            } catch (err) {
                setError("Uçak bilgileri yüklenemedi. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.");
                console.error("Uçak detayı veya parça tipleri çekilirken hata:", err);
            } finally {
                setLoadingPage(false);
            }
        };
        fetchInitialAircraftData();
    }, [token, aircraftId, isAuthenticated, navigate, authLoading]); // authLoading eklendi

    // Uçağın modeli yüklendikten ve partTypeMap hazır olduktan sonra parça seçeneklerini yükle
    useEffect(() => {
        if (originalAircraft && originalAircraft.aircraft_model && Object.keys(partTypeMap).length > 0) {
            setLoadingPartOptions(true);
            const modelIdForParts = originalAircraft.aircraft_model; // Düzenlenen uçağın modeli (değiştirilemez)

            const fetchAllPartOptions = async () => {
                const newAvailable = {};
                for (const def of PART_FIELD_DEFINITIONS) {
                    const currentSelectedPartId = formData[def.fieldKey]; // Formdaki mevcut seçim
                    let optionsForField = await fetchPartsForSpecificType(modelIdForParts, def.typeCode);
                    
                    if (currentSelectedPartId && !optionsForField.find(p => p.id === parseInt(currentSelectedPartId))) {
                        try {
                            const currentPartDetails = await axiosInstance.get(`/api/v1/envanter/parts/${currentSelectedPartId}/`);
                            if (currentPartDetails.data) {
                                optionsForField = [currentPartDetails.data, ...optionsForField];
                            }
                        } catch (err) {
                            console.warn(`Mevcut ${def.label} parçası (ID: ${currentSelectedPartId}) çekilemedi:`, err);
                        }
                    }
                    newAvailable[def.fieldKey] = optionsForField;
                }
                setAvailableParts(newAvailable);
                setLoadingPartOptions(false);
            };

            fetchAllPartOptions().catch(err => {
                setError("Parça seçenekleri yüklenirken bir sorun oluştu.");
                setLoadingPartOptions(false);
            });
        }
    }, [originalAircraft, partTypeMap, fetchPartsForSpecificType, formData]); 

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoadingPage(true); 
        const { tail_number, wing, fuselage, tail, avionics } = formData;
        
        if (!tail_number) {
            setError("Kuyruk numarası boş bırakılamaz.");
            setLoadingPage(false);
            return;
        }

        if (!wing || !fuselage || !tail || !avionics) {
            setError("Lütfen tüm parça slotları için bir parça seçin.");
            setLoadingPage(false);
            return;
        }

        const dataToSubmit = {};

        if (originalAircraft && originalAircraft.tail_number !== tail_number) {
            dataToSubmit.tail_number = tail_number;
        }

        // Parça alanlarını kontrol et
        const partFieldsToCompare = ['wing', 'fuselage', 'tail', 'avionics'];
        let hasPartChanged = false;

        partFieldsToCompare.forEach(field => {
            const formPartId = formData[field] ? parseInt(formData[field]) : null;
            const originalPartId = originalAircraft ? (originalAircraft[field] || null) : null;

            if (formPartId !== originalPartId) {
                if (formPartId) { // Kullanıcı geçerli bir parça seçmişse
                    dataToSubmit[field] = formPartId;
                    hasPartChanged = true;
                }
            }
        });

        if (Object.keys(dataToSubmit).length === 0) {
            alert("Herhangi bir değişiklik yapılmadı.");
            setLoading(false);
            return;
        }

        try {
            await updateAssembledAircraftAPI(aircraftId, dataToSubmit);
            alert('Uçak başarıyla güncellendi!');
            navigate(`/assembled-aircrafts/${aircraftId}/view`); 
        } catch (err) {
            console.error("Uçak güncelleme hatası:", err.response?.data || err.message);
            if (err.response && err.response.data) {
                let apiErrors = err.response.data;
                let errorMessages = [];
                 Object.keys(apiErrors).forEach(key => {
                    const messages = Array.isArray(apiErrors[key]) ? apiErrors[key].join(', ') : apiErrors[key];
                    const fieldLabel = PART_FIELD_DEFINITIONS.find(def => def.fieldKey === key)?.label || key.replace("_", " ").replace("aircraft model", "Uçak Modeli");
                    errorMessages.push(`${key === 'non_field_errors' ? 'Genel Hata' : fieldLabel}: ${messages}`);
                });
                setError(errorMessages.join('\n') || "Güncelleme başarısız.");
            } else {setError("Güncelleme sırasında bir hata oluştu.");}
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && isAuthenticated && user && user.profile?.team_details?.get_name_display !== 'Montaj Takımı') {
            navigate("/dashboard", { state: { error: "Bu sayfaya erişim yetkiniz yok." }, replace: true });
        }
    }, [user, isAuthenticated, authLoading, navigate]);


    if (authLoading || loadingPage) {
        return <div className="p-6 text-center text-gray-500">Uçak bilgileri yükleniyor...</div>;
    }
    if (!isAuthenticated) { // Bu genellikle MainLayout veya AdminRoute tarafından handle edilir
        return <Navigate to="/login" replace />;
    }
    if (error && !originalAircraft) { // İlk yüklemede kritik hata
        return <div className="alert-danger p-4">Hata: {error} <Link to="/assembled-aircrafts" className="underline">Listeye Dön</Link></div>;
    }
    if (!originalAircraft) { // Uçak bulunamadıysa (veya yukarıdaki error değilse)
        return <div className="p-6 text-center text-gray-500">Uçak bulunamadı veya yüklenemedi.</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-semibold text-gray-700">
                    Uçağı Düzenle: <span className="text-indigo-600">{originalAircraft.tail_number}</span>
                </h1>
                <Link to={`/assembled-aircrafts/${aircraftId}/view`} className="text-sm text-indigo-600 hover:text-indigo-800">
                    ← Detay Sayfasına Dön
                </Link>
            </div>
            
            {error && <div className="alert-danger mb-4 p-4 rounded"><pre className="whitespace-pre-wrap text-sm">{error}</pre></div>}
            
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-xl space-y-6">
                <div>
                    <label htmlFor="tail_number" className="form-label">Kuyruk Numarası <span className="text-red-500">*</span></label>
                    <input type="text" name="tail_number" id="tail_number" value={formData.tail_number} onChange={handleChange} required className="form-input mt-1" />
                </div>
                <div>
                    <p className="form-label mb-1">Uçak Modeli (Değiştirilemez)</p>
                    <input type="text" value={originalAircraft.aircraft_model_details?.name || 'Yükleniyor...'} readOnly className="form-input mt-1 bg-gray-100 cursor-not-allowed" />
                </div>

                {PART_FIELD_DEFINITIONS.map(partDef => (
                    <div key={partDef.fieldKey}>
                        <label htmlFor={partDef.fieldKey} className="form-label">
                            {partDef.label} <span className="text-red-500">*</span>
                        </label>
                        <select
                            name={partDef.fieldKey}
                            id={partDef.fieldKey}
                            value={formData[partDef.fieldKey] || ''} // formData'da değer yoksa boş string
                            onChange={handleChange}
                            required
                            disabled={loadingPartOptions || loadingPage} // Genel yükleme veya parça seçenekleri yüklenirken
                            className="form-select mt-1 disabled:bg-gray-200"
                        >
                            <option value="">
                                {loadingPartOptions ? 'Seçenekler Yükleniyor...' : `${partDef.label} Seçiniz...`}
                            </option>
                            {(availableParts[partDef.fieldKey] || []).map(p => (
                                <option key={p.id} value={p.id}>
                                    {p.serial_number} ({p.part_type_name} / Mod: {p.aircraft_model_compatibility_name}) {p.status !== 'STOKTA' ? `(${p.status_display} - Mevcut Takılı)` : ''}
                                </option>
                            ))}
                        </select>
                         {originalAircraft && (availableParts[partDef.fieldKey] || []).length === 0 && !loadingPartOptions && !loadingPage && (
                            <p className="text-xs text-red-500 mt-1">Bu model için uygun {partDef.label.toLowerCase()} bulunamadı veya stokta yok.</p>
                        )}
                    </div>
                ))}
                
                <div className="flex justify-end pt-4">
                    <button type="button" onClick={() => navigate(`/assembled-aircrafts/${aircraftId}/view`)} disabled={submittingForm} className="btn-secondary mr-3">İptal</button>
                    <button type="submit" disabled={submittingForm || loadingPartOptions || loadingPage} className="btn-primary disabled:opacity-50">
                        {submittingForm ? 'Kaydediliyor...' : 'Değişiklikleri Kaydet'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default AssembledAircraftEditPage;