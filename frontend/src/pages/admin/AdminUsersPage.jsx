import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import DataTable from 'react-data-table-component';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';


const customTableStyles = { /* ... */ };
const paginationComponentOptions = { /* ... */ };

/**
 * Adminlerin sistemdeki kullanıcıları listelemesi ve yönetmesi için sayfa bileşeni.
 * Server-side data işlemleri için `react-data-table-component` kullanır.
 */
function AdminUsersPage() {
    const { token, isAuthenticated, loading: authLoading } = useAuth();
    const navigate = useNavigate();

    const [data, setData] = useState([]);
    const [loadingApi, setLoadingApi] = useState(true);
    const [totalRows, setTotalRows] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage, setPerPage] = useState(10);
    const [sortField, setSortField] = useState("username"); 
    const [sortOrder, setSortOrder] = useState("asc");
    const [searchTerm, setSearchTerm] = useState('');
    const [resetPaginationToggle, setResetPaginationToggle] = useState(false);
    const [apiError, setApiError] = useState('');
    const dtRef = useRef(null);

    const fetchUsers = useCallback(async (currentPage, currentPerPage, currentSortField, currentSortOrder, currentSearchTerm) => {
        if (!isAuthenticated || !token) {
            setLoadingApi(false);
            return;
        }
        setLoadingApi(true);
        const orderingParam = `${currentSortOrder === "desc" ? "-" : ""}${currentSortField}`;
        let apiUrl = `/api/v1/users/users/?page=${currentPage}&page_size=${currentPerPage}&ordering=${orderingParam}`;
        if (currentSearchTerm) {
            apiUrl += `&search=${encodeURIComponent(currentSearchTerm)}`;
        }
        
        try {
            const res = await fetch(apiUrl, { headers: { Authorization: `Token ${token}` } });
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            const json = await res.json();
            
            if (json.results && typeof json.count !== 'undefined') {
                setData(json.results);
                setTotalRows(json.count);
            } else if (json.data && typeof json.recordsTotal !== 'undefined') {
                setData(json.data);
                setTotalRows(json.recordsTotal);
            } else {
                setData([]); setTotalRows(0);
            }
            setApiError('');
        } catch (err) {
            console.error("Kullanıcı verileri çekilirken hata:", err);
            setData([]); setTotalRows(0); setApiError(err.message);
        } finally {
            setLoadingApi(false);
        }
    }, [token, isAuthenticated]);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchUsers(page, perPage, sortField, sortOrder, searchTerm);
        }
    }, [page, perPage, sortField, sortOrder, searchTerm, fetchUsers, authLoading, isAuthenticated]);

    const handlePageChange = useCallback(newPage => setPage(newPage), []);
    const handlePerRowsChange = useCallback((newPerPage, newPage) => {
        setPerPage(newPerPage); setPage(newPage);
    }, []);
    const handleSort = useCallback((column, sortDirection) => {
        if (column.sortField) {
            setSortField(column.sortField); setSortOrder(sortDirection); setPage(1);
        }
    }, []);
     const handleSearch = useCallback((event) => {
        setSearchTerm(event.target.value);
        setPage(1);
        setResetPaginationToggle(prev => !prev);
    }, []);

    const columns = useMemo(() => [
        { name: "ID", selector: row => row.id, sortable: true, sortField: "id", omit: true },
        { name: "Kullanıcı Adı", selector: row => row.username, sortable: true, sortField: "username", wrap: true },
        { name: "E-posta", selector: row => row.email, sortable: true, sortField: "email", wrap: true },
        { name: "Ad", selector: row => row.first_name, sortable: true, sortField: "first_name" },
        { name: "Soyad", selector: row => row.last_name, sortable: true, sortField: "last_name" },
        { name: "Takımı", selector: row => row.profile?.team_details?.get_name_display || 'Takımsız', sortable: false }, // profile.team__name ile sıralanabilir
        { name: "Aktif?", selector: row => row.is_active, sortable: true, sortField: "is_active", cell: row => row.is_active ? <span className="text-green-600">Evet</span> : <span className="text-red-600">Hayır</span> },
        { name: "Admin?", selector: row => row.is_staff, sortable: true, sortField: "is_staff", cell: row => row.is_staff ? <span className="text-green-600">Evet</span> : <span className="text-red-600">Hayır</span> },
        {
            name: "İşlemler",
            button: true,
            cell: row => (
                <div className="flex gap-x-1">
                    <button title="Düzenle (Profil)" className="p-1 text-blue-600 hover:text-blue-800" onClick={() => navigate(`/admin/users/${row.id}/profile/edit`)}>✏️</button>
                    {/* TODO: Kullanıcı aktif/pasif yapma butonu */}
                </div>
            )
        }
    ], [navigate]);

    if (authLoading) return <div className="p-6 text-center">Yükleniyor...</div>;
    
    return (
        <div className="container mx-auto p-4 xl:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                <h1 className="text-3xl font-semibold text-gray-700">Kullanıcı Yönetimi</h1>
                 <input
                    type="text"
                    placeholder="Kullanıcı adı, email ara..."
                    className="form-input px-4 py-2 border border-gray-300 rounded-md shadow-sm w-full sm:w-auto"
                    onChange={handleSearch}
                />
            </div>
            {apiError && <div className="alert-danger mb-4">{apiError}</div>}
            <div className="bg-white p-0 sm:p-2 rounded-xl shadow-xl overflow-x-auto">
                <DataTable
                    columns={columns}
                    data={data}
                    progressPending={loadingApi}
                    progressComponent={<div className="py-10 text-center text-gray-500">Kullanıcılar yükleniyor...</div>}
                    pagination
                    paginationServer
                    paginationTotalRows={totalRows}
                    onChangeRowsPerPage={handlePerRowsChange}
                    onChangePage={handlePageChange}
                    paginationResetDefaultPage={resetPaginationToggle}
                    sortServer
                    onSort={handleSort}
                    defaultSortFieldId={columns.findIndex(col => col.sortField === "username") + 1 || 1}
                    defaultSortAsc={true}
                    highlightOnHover
                    striped
                    responsive
                    noDataComponent={<div className="py-10 text-center text-gray-500">Gösterilecek kullanıcı bulunamadı.</div>}
                />
            </div>
        </div>
    );
}
export default AdminUsersPage;