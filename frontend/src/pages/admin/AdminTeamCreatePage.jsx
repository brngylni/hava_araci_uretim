import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { createTeamAPI } from '../../api/teamService';
import axiosInstance from '../../api/axiosInstance'; 

// Team modelindeki choices'ı frontend'e taşımak veya API'den almak
const TEAM_TYPE_CHOICES = [
    { value: 'KANAT', label: 'Kanat Takımı' },
    { value: 'GOVDE', label: 'Gövde Takımı' },
    { value: 'KUYRUK', label: 'Kuyruk Takımı' },
    { value: 'AVIYONIK', label: 'Aviyonik Takımı' },
    { value: 'MONTAJ', label: 'Montaj Takımı' },
];

function AdminTeamCreatePage() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '', // Takım tipi/adı (KANAT, GOVDE vb.)
        responsible_part_type: '', // PartType ID'si
    });
    const [partTypes, setPartTypes] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!token) return;
        const fetchPartTypes = async () => {
            try {
                const res = await axiosInstance.get('/api/v1/envanter/part-types/');
                setPartTypes(res.data.results || res.data || []);
            } catch (err) {
                setError("Parça tipleri yüklenemedi.");
            }
        };
        fetchPartTypes();
    }, [token]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const dataToSubmit = { ...formData };
        if (!dataToSubmit.name) {
            setError("Takım adı (tipi) seçilmelidir.");
            setLoading(false);
            return;
        }
        // Montaj takımı değilse ve responsible_part_type boşsa null gönder,
        // serializer bunu "zorunlu" olarak handle eder.
        if (dataToSubmit.name !== 'MONTAJ' && !dataToSubmit.responsible_part_type) {
             dataToSubmit.responsible_part_type = null; 
        } else if (dataToSubmit.name === 'MONTAJ') {
            dataToSubmit.responsible_part_type = null; // Montaj takımı için her zaman null
        }
        
        if (dataToSubmit.responsible_part_type) {
            dataToSubmit.responsible_part_type = parseInt(dataToSubmit.responsible_part_type, 10);
        }


        try {
            await createTeamAPI(dataToSubmit); // Token axiosInstance ile otomatik ekleniyor
            alert('Takım başarıyla oluşturuldu!');
            navigate('/admin/teams');
        } catch (err) {
            if (err.response && err.response.data) {
                let apiErrors = err.response.data;
                let errorMessages = [];
                Object.keys(apiErrors).forEach(key => {
                    const messages = Array.isArray(apiErrors[key]) ? apiErrors[key].join(', ') : apiErrors[key];
                    errorMessages.push(`${key === 'non_field_errors' ? 'Genel Hata' : key}: ${messages}`);
                });
                setError(errorMessages.join('\n') || "Takım oluşturulamadı.");
            } else {
                setError("Takım oluşturulurken bir hata oluştu.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-semibold text-gray-700 mb-6">Yeni Takım Ekle</h1>
            {error && <div className="alert-danger mb-4"><pre>{error}</pre></div>}
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-xl space-y-6">
                <div>
                    <label htmlFor="name" className="form-label">Takım Adı (Tipi) <span className="text-red-500">*</span></label>
                    <select name="name" id="name" value={formData.name} onChange={handleChange} required className="form-select">
                        <option value="">Tip Seçiniz...</option>
                        {TEAM_TYPE_CHOICES.map(choice => (
                            <option key={choice.value} value={choice.value}>{choice.label}</option>
                        ))}
                    </select>
                </div>

                {formData.name && formData.name !== 'MONTAJ' && (
                    <div>
                        <label htmlFor="responsible_part_type" className="form-label">Sorumlu Olduğu Parça Tipi <span className="text-red-500">*</span></label>
                        <select
                            name="responsible_part_type"
                            id="responsible_part_type"
                            value={formData.responsible_part_type}
                            onChange={handleChange}
                            required={formData.name !== 'MONTAJ'}
                            className="form-select"
                        >
                            <option value="">Parça Tipi Seçiniz...</option>
                            {partTypes.map(pt => (
                                <option key={pt.id} value={pt.id}>{pt.get_name_display}</option>
                            ))}
                        </select>
                    </div>
                )}
                <div className="flex justify-end pt-4">
                    <button type="button" onClick={() => navigate('/admin/teams')} disabled={loading} className="btn-secondary mr-3">İptal</button>
                    <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50">
                        {loading ? 'Kaydediliyor...' : 'Takımı Oluştur'}
                    </button>
                </div>
            </form>
        </div>
    );
}
export default AdminTeamCreatePage;