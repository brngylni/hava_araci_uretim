import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getTeamByIdAPI, updateTeamAPI } from '../../api/teamService';
import axiosInstance from '../../api/axiosInstance';

const TEAM_TYPE_CHOICES = [ 
    { value: 'KANAT', label: 'Kanat Takımı' },
    { value: 'GOVDE', label: 'Gövde Takımı' },
    { value: 'KUYRUK', label: 'Kuyruk Takımı' },
    { value: 'AVIYONIK', label: 'Aviyonik Takımı' },
    { value: 'MONTAJ', label: 'Montaj Takımı' },
];

function AdminTeamEditPage() {
    const { teamId } = useParams();
    const { token } = useAuth();
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        name: '',
        responsible_part_type: '',
    });
    const [partTypes, setPartTypes] = useState([]);
    const [originalTeamName, setOriginalTeamName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true); // Başlangıçta veri çekme için true

    useEffect(() => {
        if (!token || !teamId) return;
        setLoading(true);
        const fetchInitialData = async () => {
            try {
                const [teamRes, ptRes] = await Promise.all([
                    getTeamByIdAPI(teamId),
                    axiosInstance.get('/api/v1/envanter/part-types/')
                ]);
                
                const teamData = teamRes;
                setFormData({
                    name: teamData.name,
                    responsible_part_type: teamData.responsible_part_type || '', // null ise boş string
                });
                setOriginalTeamName(teamData.name); // name (tip) değişikliğini kontrol etmek için
                setPartTypes(ptRes.data.results || ptRes.data || []);
                setError('');
            } catch (err) {
                console.error("Veri çekilirken hata:", err);
                setError("Takım veya parça tipi verileri yüklenemedi.");
            } finally {
                setLoading(false);
            }
        };
        fetchInitialData();
    }, [token, teamId]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const dataToSubmit = { ...formData };
        
        if (dataToSubmit.name !== 'MONTAJ' && !dataToSubmit.responsible_part_type) {
            setError("Üretim takımları için sorumlu parça tipi seçilmelidir.");
            setLoading(false);
            return;
        } else if (dataToSubmit.name === 'MONTAJ') {
            dataToSubmit.responsible_part_type = null;
        }

        if (dataToSubmit.responsible_part_type) {
            dataToSubmit.responsible_part_type = parseInt(dataToSubmit.responsible_part_type, 10);
        }
        
        // Sadece sorumlu parça tipini güncelle
        const payload = {
            responsible_part_type: dataToSubmit.responsible_part_type
        };

        try {
            await updateTeamAPI(teamId, payload);
            alert('Takım başarıyla güncellendi!');
            navigate('/admin/teams');
        } catch (err) {
            if (err.response && err.response.data) {
                let apiErrors = err.response.data;
                let errorMessages = [];
                Object.keys(apiErrors).forEach(key => {
                    const messages = Array.isArray(apiErrors[key]) ? apiErrors[key].join(', ') : apiErrors[key];
                    errorMessages.push(`${key === 'non_field_errors' ? 'Genel Hata' : key}: ${messages}`);
                });
                setError(errorMessages.join('\n') || "Takım güncellenemedi.");
            } else {
                setError("Takım güncellenirken bir hata oluştu.");
            }
        } finally {
            setLoading(false);
        }
    };

    if (loading && !formData.name) { // Veri henüz yüklenmemişse
        return <div className="p-6 text-center">Takım bilgileri yükleniyor...</div>;
    }
    if (error && !formData.name) { // İlk yüklemede hata varsa formu gösterme
         return <div className="alert-danger p-4">Hata: {error} <Link to="/admin/teams" className="underline">Listeye Dön</Link></div>;
    }


    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-semibold text-gray-700 mb-6">Takımı Düzenle: {originalTeamName}</h1>
            {error && <div className="alert-danger mb-4"><pre>{error}</pre></div>}
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-xl space-y-6">
                <div>
                    <label htmlFor="name_display" className="form-label">Takım Adı (Tipi)</label>
                    <input 
                        type="text" 
                        id="name_display" 
                        value={TEAM_TYPE_CHOICES.find(c => c.value === formData.name)?.label || formData.name} 
                        readOnly 
                        className="form-input bg-gray-100"
                    />
                    <p className="text-xs text-gray-500 mt-1">Takım tipi (adı) değiştirilemez.</p>
                </div>

                {formData.name && formData.name !== 'MONTAJ' && (
                    <div>
                        <label htmlFor="responsible_part_type" className="form-label">Sorumlu Olduğu Parça Tipi <span className="text-red-500">*</span></label>
                        <select
                            name="responsible_part_type"
                            id="responsible_part_type"
                            value={formData.responsible_part_type || ''} // null ise boş string yap
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
                        {loading ? 'Kaydediliyor...' : 'Değişiklikleri Kaydet'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default AdminTeamEditPage;