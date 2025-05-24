import axiosInstance from './axiosInstance'; // Bir önceki adımda oluşturduğumuz instance

/**
 * Kullanıcıyı API üzerinden giriş yaptırır.
 * @param {string} username Kullanıcının kullanıcı adı.
 * @param {string} password Kullanıcının şifresi.
 * @returns {Promise<object>} Giriş başarılıysa kullanıcı bilgileri ve token içeren obje.
 * @throws {Error} Giriş başarısız olursa hata fırlatır.
 */
export const loginUser = async (username, password) => {
    const response = await axiosInstance.post('/api/v1/users/login/', { username, password });
    return response.data; // { token, user } döner
};

/**
 * Yeni kullanıcı kaydı oluşturur.
 * @param {object} userData Yeni kullanıcı bilgileri: { username, email, password, password2, first_name, last_name, team_id (opsiyonel) }
 * @returns {Promise<object>} Başarılı kayıt durumunda oluşturulan kullanıcıya ait bilgiler (şifre hariç).
 * @throws {Error} Kayıt işlemi başarısız olursa hata detaylarıyla birlikte fırlatır.
 */
export const registerUser = async (userData) => {
    try {
        const response = await axiosInstance.post('/api/v1/users/register/', userData);
        return response.data;
    } catch (error) {
        console.error("Registration failed:", error.response ? error.response.data : error.message);
        throw error; // Hata detaylarını çağıran bileşene iletmek için
    }
};

/**
 * Giriş yapmış kullanıcının bilgilerini çeker.
 * @returns {Promise<object>} Oturum açmış kullanıcıya ait bilgiler.
 * @throws {Error} Kullanıcı bilgileri çekilemezse hata fırlatır.
 */
export const fetchCurrentUser = async () => {
    const response = await axiosInstance.get('/api/v1/users/users/me/');
    return response.data;
};
