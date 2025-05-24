import axiosInstance from './axiosInstance';

/**
 * Yeni bir takım oluşturur.
 * @param {object} teamData Takıma ait veriler (örneğin: takım adı, takım tipi vb.).
 * @returns {Promise<object>} Oluşturulan takıma ait bilgiler.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const createTeamAPI = async (teamData) => {
    try {
        const response = await axiosInstance.post('/api/v1/uretim/teams/', teamData);
        return response.data;
    } catch (error) {
        console.error("Takım oluşturma hatası:", error.response?.data || error.message);
        throw error;
    }
};

/**
 * Belirli bir takımın detaylarını ID’ye göre çeker.
 * @param {string|number} teamId Detayı istenen takımın ID’si.
 * @returns {Promise<object>} Takıma ait detaylı bilgi.
 * @throws {Error} API isteği başarısız olursa veya takım bulunamazsa hata fırlatır.
 */
export const getTeamByIdAPI = async (teamId) => {
    try {
        const response = await axiosInstance.get(`/api/v1/uretim/teams/${teamId}/`);
        return response.data;
    } catch (error) {
        console.error(`Takım detayı çekilirken hata (ID: ${teamId}):`, error.response?.data || error.message);
        throw error;
    }
};

/**
 * Mevcut bir takımı günceller.
 * @param {string|number} teamId Güncellenecek takımın ID’si.
 * @param {object} teamData Güncellenecek takım bilgileri.
 * @returns {Promise<object>} Güncellenmiş takım verisi.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const updateTeamAPI = async (teamId, teamData) => {
    try {
        const response = await axiosInstance.patch(`/api/v1/uretim/teams/${teamId}/`, teamData);
        return response.data;
    } catch (error) {
        console.error(`Takım güncellenirken hata (ID: ${teamId}):`, error.response?.data || error.message);
        throw error;
    }
};

/**
 * Belirli bir takımı ID’ye göre siler.
 * @param {string|number} teamId Silinecek takımın ID’si.
 * @returns {Promise<object>} Silme işleminin HTTP yanıtı (başarılıysa 204 No Content).
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const deleteTeamAPI = async (teamId) => {
    try {
        const response = await axiosInstance.delete(`/api/v1/uretim/teams/${teamId}/`);
        return response;
    } catch (error) {
        console.error(`Takım silinirken hata (ID: ${teamId}):`, error.response?.data || error.message);
        throw error;
    }
};
