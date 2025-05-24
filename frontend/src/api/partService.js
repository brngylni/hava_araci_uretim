import axiosInstance from './axiosInstance';

/**
 * Yeni bir parça oluşturur.
 * @param {object} partData Oluşturulacak parçaya ait veriler (örneğin: seri numarası, tipi, üretim takımı vs.).
 * @returns {Promise<object>} Oluşturulan parçaya ait bilgiler.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const createPart = async (partData) => {
    try {
        const response = await axiosInstance.post('/api/v1/envanter/parts/', partData);
        return response.data;
    } catch (error) {
        console.error("Failed to create part:", error.response ? error.response.data : error.message);
        throw error;
    }
};

/**
 * Belirli bir parçayı ID'sine göre getirir.
 * @param {string|number} partId Getirilecek parçanın ID'si.
 * @returns {Promise<object>} İlgili parçaya ait detaylar.
 * @throws {Error} API isteği başarısız olursa veya parça bulunamazsa hata fırlatır.
 */
export const getPartByIdAPI = async (partId) => {
    try {
        const response = await axiosInstance.get(`/api/v1/envanter/parts/${partId}/`);
        return response.data;
    } catch (error) {
        console.error(`Failed to fetch part ${partId}:`, error.response ? error.response.data : error.message);
        throw error;
    }
};

/**
 * Bir parçayı geri dönüşüm işlemine gönderir.
 * @param {string|number} partId Geri dönüşüme gönderilecek parçanın ID'si.
 * @returns {Promise<object>} Geri dönüşüm işleminin sonucu.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const recyclePart = async (partId) => {
    try {
        const response = await axiosInstance.post(`/api/v1/envanter/parts/${partId}/recycle/`);
        return response.data;
    } catch (error) {
        console.error(`Failed to recycle part ${partId}:`, error.response ? error.response.data : error.message);
        throw error;
    }
};

// Diğer parça işlemleri (get_by_id, update, delete) buraya eklenebilir.
