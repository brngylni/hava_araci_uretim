import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from "react-router-dom";

function DashboardPage() {
    const { user } = useAuth(); // Sadece user bilgisine ihtiyacımız var

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6 text-gray-800">Ana Panel</h1>
            {user ? (
                <div className="bg-white p-6 rounded-lg shadow">
                    <p className="text-xl text-gray-700">
                        Hoş geldin, <span className="font-semibold">{user.first_name || user.username}</span>!
                    </p>
                    <p className="text-gray-600 mt-2">
                        Takımın: <span className="font-medium">{user.profile?.team_details?.get_name_display || 'Belirtilmemiş'}</span>
                    </p>
                    <p className="mt-4 text-gray-600">
                        Bu panelden hava aracı üretim süreçlerini takip edebilir ve yönetebilirsiniz.
                        Sol menüden ilgili bölümlere ulaşabilirsiniz.
                    </p>
                </div>
            ) : (
                <p>Kullanıcı bilgileri yükleniyor...</p>
            )}

            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Link to="/parts" className='h-full'>
                    <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow h-full">
                        <h2 className="text-xl font-semibold text-gray-700 mb-2">Parça Envanteri</h2>
                        <p className="text-gray-600">Mevcut parçaları görüntüleyin, yeni parçalar üretin veya geri dönüşüme gönderin.</p>
                    </div>
                </Link>
                <Link to="/assembled-aircrafts" className='h-full'>
                    <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow h-full">
                        <h2 className="text-xl font-semibold text-gray-700 mb-2">Uçak Montajı</h2>
                        <p className="text-gray-600">Monte edilmiş uçakları listeleyin ve yeni uçaklar monte edin.</p>
                    </div>
                </Link>
                <Link to="/missing-parts" className='h-full'>
                    <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow h-full">
                        <h2 className="text-xl font-semibold text-gray-700 mb-2">Eksik Parça Kontrolü</h2>
                        <p className="text-gray-600">Belirli uçak modelleri için envanterdeki eksik parçaları kontrol edin.</p>
                    </div>
                </Link>
            </div>
        </div>
    );
}

export default DashboardPage;