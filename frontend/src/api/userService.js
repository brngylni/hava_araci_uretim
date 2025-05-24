import axiosInstance from './axiosInstance';

/**
 * Belirli bir kullanıcı profiline ait verileri ID ile getirir.
 * @param {string|number} profileId Getirilecek kullanıcı profilinin ID’si.
 * @returns {Promise<object>} Kullanıcı profiline ait bilgiler.
 * @throws {Error} API isteği başarısız olursa veya profil bulunamazsa hata fırlatır.
 */
export const getUserProfileByIdAPI = async (profileId) => {
    try {
        const response = await axiosInstance.get(`/api/v1/users/profiles/${profileId}/`);
        return response.data;
    } catch (error) {
        console.error(`Kullanıcı profili çekilirken hata (ID: ${profileId}):`, error.response?.data || error.message);
        throw error;
    }
};

/**
 * Kullanıcı profilini günceller (partial update).
 * @param {string|number} profileId Güncellenecek kullanıcı profilinin ID’si.
 * @param {object} profileData Güncellenecek profil verileri (örneğin: telefon, departman vb.).
 * @returns {Promise<object>} Güncellenmiş kullanıcı profili bilgileri.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const updateUserProfileAPI = async (profileId, profileData) => {
    try {
        const response = await axiosInstance.patch(`/api/v1/users/profiles/${profileId}/`, profileData);
        return response.data;
    } catch (error) {
        console.error(`Kullanıcı profili güncellenirken hata (ID: ${profileId}):`, error.response?.data || error.message);
        throw error;
    }
};
