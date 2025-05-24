import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import MainLayout from './components/layout/MainLayout';
import { useAuth } from './contexts/AuthContext';
import PartsListPage from './pages/PartsListPage';
import PartCreatePage from "./pages/PartCreatePage"
import AircraftAssemblyPage from './pages/AircraftAssemblyPage';
import AssembledAircraftsPage from './pages/AssembledAircraftsPage';
import PartDetailPage from './pages/PartDetailPage';
import MissingPartsPage from './pages/MissingPartsPage';
import AssembledAircraftEditPage from './pages/AssembledAircraftEditPage';
import AdminTeamsPage from './pages/admin/AdminTeamsPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminUserProfileEditPage from './pages/admin/AdminUserProfileEditPage';
import AssembledAircraftDetailPage from './pages/AssembledAircraftDetailPage';
import AdminPartTypesPage from './pages/admin/AdminPartTypesPage';
import AdminAircraftModelsPage from './pages/admin/AdminAircraftModelsPage';

const AdminRoute = () => {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return <div>Yükleniyor...</div>;
  // Hem authenticated hem de is_staff (admin) olmalı
  return isAuthenticated && user?.is_staff ? <Outlet /> : <Navigate to="/dashboard" state={{ error: "Bu sayfaya erişim yetkiniz yok." }} replace />;
};

function App() {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl">Uygulama Yükleniyor...</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" />} />
      <Route path="/register" element={!isAuthenticated ? <RegisterPage /> : <Navigate to="/dashboard" />} />
      <Route
        path="/"
        element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" replace />}
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="parts" element={<PartsListPage />} />
        <Route path="parts/new" element={<PartCreatePage />} />
        <Route path="parts/:partId/view" element={<PartDetailPage />} />


        <Route element={<AdminRoute />}> {/* AdminRoute wrapper'ı */}
          <Route path="admin/teams" element={<AdminTeamsPage />} />
          <Route path="admin/users" element={<AdminUsersPage />} />
          <Route path="admin/users/:userId/profile/edit" element={<AdminUserProfileEditPage />} />
          <Route path="admin/part-types" element={<AdminPartTypesPage />} />
          <Route path="admin/aircraft-models" element={<AdminAircraftModelsPage />} />
        </Route>
        <Route path="assembled-aircrafts" element={<AssembledAircraftsPage />} />
        <Route path="assembled-aircrafts/new" element={<AircraftAssemblyPage />} />
        <Route path="assembled-aircrafts" element={<AssembledAircraftsPage />} />
        <Route path="assembled-aircrafts/:aircraftId/edit" element={<AssembledAircraftEditPage />} />
        <Route path="assembled-aircrafts/:aircraftId/view" element={<AssembledAircraftDetailPage />} />
        <Route path="missing-parts" element={<MissingPartsPage />} />
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
}

export default App;