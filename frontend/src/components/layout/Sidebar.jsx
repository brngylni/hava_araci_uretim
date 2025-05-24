import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function Sidebar() {
    const { user } = useAuth(); // Kullanıcı rolüne/takımına göre menü elemanları gösterilebilir

    const menuItems = [
        { name: 'Dashboard', path: '/dashboard', icon: '📊' }, 
        { name: 'Parça Envanteri', path: '/parts', icon: '🔩' },
        { name: 'Monte Edilmiş Uçaklar', path: '/assembled-aircrafts', icon: '✈️' },
        { name: 'Eksik Parçalar', path: '/missing-parts', icon: '❓' },
    ];

    // Admin'e özel menü elemanları
    const adminMenuItems = [
        { name: 'Kullanıcı Yönetimi', path: '/admin/users', icon: '👥' },
        { name: 'Takım Yönetimi', path: '/admin/teams', icon: '🛠️' },
        { name: 'Parça Tipi', path: '/admin/part-types', icon: '⚙️' },
        { name: 'Uçak Tipi', path: '/admin/aircraft-models', icon: '🛩️' },
    ];

    const activeClassName = "bg-gray-700 text-white";
    const inactiveClassName = "text-gray-300 hover:bg-gray-700 hover:text-white";

    return (
        <aside className="w-64 bg-gray-900 text-white min-h-screen p-4 space-y-2">
            <div className="text-2xl font-semibold p-2 mb-5 border-b border-gray-700">
                Menu
            </div>
            {menuItems.map((item) => (
                <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) =>
                        `block py-2.5 px-4 rounded transition duration-200 ${isActive ? activeClassName : inactiveClassName}`
                    }
                >
                    <span className="mr-2">{item.icon}</span>
                    {item.name}
                </NavLink>
            ))}

            {/* Admin Kullanıcılar için ek menü elemanları */}
            {user && user.is_staff && ( // UserSerializer'ınızın is_staff döndürdüğünden emin olun
                <>
                    <div className="pt-4 mt-4 space-y-2 border-t border-gray-700">
                        <p className="px-4 text-xs uppercase text-gray-500">Admin Paneli</p>
                        {adminMenuItems.map((item) => (
                            <NavLink
                                key={item.name}
                                to={item.path}
                                className={({ isActive }) =>
                                    `block py-2.5 px-4 rounded transition duration-200 ${isActive ? activeClassName : inactiveClassName}`
                                }
                            >
                                <span className="mr-2">{item.icon}</span>
                                {item.name}
                            </NavLink>
                        ))}
                    </div>
                </>
            )}
        </aside>
    );
}

export default Sidebar;