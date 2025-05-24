import axiosInstance from './axiosInstance';

/**
 * Yeni bir parça tipi oluşturur.
 * @param {object} partTypeData Oluşturulacak parça tipine ait veriler (örneğin: isim, açıklama vs.).
 * @returns {Promise<object>} Oluşturulan parça tipine ait bilgiler.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const createPartTypeAPI = async (partTypeData) => {
    try {
        const response = await axiosInstance.post('/api/v1/envanter/part-types/', partTypeData);
        return response.data;
    } catch (error) {
        console.error("Parça Tipi oluşturma hatası:", error.response?.data || error.message);
        throw error;
    }
};

/**
 * Belirli bir parça tipini ID'sine göre siler.
 * @param {string|number} partTypeId Silinecek parça tipinin ID'si.
 * @returns {Promise<object>} Silme işleminin HTTP yanıtı (başarılıysa 204 No Content).
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const deletePartTypeAPI = async (partTypeId) => {
    try {
        const response = await axiosInstance.delete(`/api/v1/envanter/part-types/${partTypeId}/`);
        return response;
    } catch (error) {
        console.error(`Parça Tipi silme hatası (ID: ${partTypeId}):`, error.response?.data || error.message);
        throw error;
    }
};
