/**
 * Uçak modellerini filtrelenmiş şekilde API'den çeker.
 * @param {object} params API isteğinde kullanılacak filtreleme, sıralama veya sayfalama parametreleri.
 * @returns {Promise<object>} API'den dönen uçak modelleri verisi.
 * @throws {Error} API isteği başarısız olursa hata fırlatır.
 */
export const fetchAircraftModelsAPI = async (params) => {
    try {
        const response = await axiosInstance.get('/api/v1/envanter/aircraft-models/', { params });
        return response.data;
    } catch (error) {
        console.error("Uçak modelleri çekilirken hata:", error.response?.data || error.message);
        throw error;
    }
};
