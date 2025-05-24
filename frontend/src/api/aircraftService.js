import axiosInstance from './axiosInstance'; // Temel axios instance'ımız

const API_BASE_URL_MONTAJ = '/api/v1/montaj/assembled-aircrafts'; // Sık kullanılan base URL

/**
 * Belirli bir monte edilmiş uçağın detaylarını API'den çeker.
 * @param {string|number} aircraftId Çekilecek uçağın ID'si.
 * @returns {Promise<object>} Uçak detaylarını içeren obje.
 * @throws {Error} API isteği başarısız olursa veya veri bulunamazsa.
 */
export const getAssembledAircraftByIdAPI = async (aircraftId) => {
    try {
        const response = await axiosInstance.get(`${API_BASE_URL_MONTAJ}/${aircraftId}/`);
        return response.data;
    } catch (error) {
        const errorMessage = error.response?.data?.detail || error.response?.data?.error || `Monte edilmiş uçak detayı (ID: ${aircraftId}) çekilirken bir hata oluştu.`;
        console.error(errorMessage, error.response?.data || error);
        throw new Error(errorMessage);
    }
};

/**
 * Mevcut bir monte edilmiş uçağın bilgilerini günceller (PATCH isteği).
 * @param {string|number} aircraftId Güncellenecek uçağın ID'si.
 * @param {object} aircraftData Güncellenecek alanları içeren obje (örn: { tail_number: "TC-NEW" }).
 * @returns {Promise<object>} Güncellenmiş uçak detaylarını içeren obje.
 * @throws {Error} API isteği başarısız olursa.
 */
export const updateAssembledAircraftAPI = async (aircraftId, aircraftData) => {
    try {
        const response = await axiosInstance.patch(`${API_BASE_URL_MONTAJ}/${aircraftId}/`, aircraftData);
        return response.data;
    } catch (error) {
        const errorMessage = error.response?.data || `Monte edilmiş uçak (ID: ${aircraftId}) güncellenirken bir hata oluştu.`;
        console.error("Update Assembled Aircraft Error:", errorMessage, error.response?.data || error);
        // Hata objesini doğrudan fırlatmak, component'te daha detaylı işlemeye olanak tanır
        throw error; 
    }
};

/**
 * Belirli bir monte edilmiş uçağı API'den siler.
 * @param {string|number} aircraftId Silinecek uçağın ID'si.
 * @returns {Promise<object>} Başarılı silme sonrası API yanıtı (genellikle boş veya status 204).
 * @throws {Error} API isteği başarısız olursa.
 */
export const deleteAssembledAircraftAPI = async (aircraftId) => {
    try {
        const response = await axiosInstance.delete(`${API_BASE_URL_MONTAJ}/${aircraftId}/`);
        return response; // Başarılı silmede 204 No Content döner, response.data genellikle olmaz.
    } catch (error) {
        const errorMessage = error.response?.data?.detail || error.response?.data?.error || `Monte edilmiş uçak (ID: ${aircraftId}) silinirken bir hata oluştu.`;
        console.error(errorMessage, error.response?.data || error);
        throw new Error(errorMessage);
    }
};

/**
 * Belirli bir uçak modeli için envanterdeki eksik temel parçaları kontrol eder.
 * @param {string} aircraftModelName Kontrol edilecek uçak modelinin adı (örn: "TB2").
 * @returns {Promise<object>} Eksik parça bilgilerini içeren obje.
 * @throws {Error} API isteği başarısız olursa.
 */
export const checkMissingPartsAPI = async (aircraftModelName) => {
    try {
        const response = await axiosInstance.get(`${API_BASE_URL_MONTAJ}/check_missing_parts/?aircraft_model_name=${encodeURIComponent(aircraftModelName)}`);
        return response.data;
    } catch (error) {
        const errorMessage = error.response?.data?.detail || error.response?.data?.error || `${aircraftModelName} için eksik parça kontrolü sırasında bir hata oluştu.`;
        console.error(errorMessage, error.response?.data || error);
        throw new Error(errorMessage);
    }
};

/**
 * Yeni bir uçak monte etmek için API'ye POST isteği gönderir.
 * @param {object} assemblyData Montaj için gerekli verileri içeren obje
 * (örn: { tail_number, aircraft_model, wing, fuselage, tail, avionics }).
 * @returns {Promise<object>} Oluşturulan yeni uçağın bilgileri.
 * @throws {Error} API isteği başarısız olursa.
 */
export const assembleNewAircraftAPI = async (assemblyData) => {
    try {
        const response = await axiosInstance.post(`${API_BASE_URL_MONTAJ}/`, assemblyData);
        return response.data;
    } catch (error) {
        const errorMessage = error.response?.data || "Yeni uçak montajı sırasında bir hata oluştu.";
        console.error("Assemble New Aircraft Error:", errorMessage, error.response?.data || error);
        throw error; // Hata objesini component'in işlemesi için fırlat
    }
};

