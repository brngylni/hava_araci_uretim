import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import DataTable from 'react-data-table-component';
import { useAuth } from '../../contexts/AuthContext';

/**
 * Adminlerin sistemdeki uçak modellerini listelemesi için sayfa bileşeni.
 */
function AdminAircraftModelsPage() {
    const { token, isAuthenticated, loading: authLoading } = useAuth();

    const [data, setData] = useState([]);
    const [loadingApi, setLoadingApi] = useState(true);
    const [totalRows, setTotalRows] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage, setPerPage] = useState(10);
    const [sortField, setSortField] = useState("name"); 
    const [sortOrder, setSortOrder] = useState("asc");
    const [searchTerm, setSearchTerm] = useState(''); // Genel arama için
    const [resetPaginationToggle, setResetPaginationToggle] = useState(false);
    const [apiError, setApiError] = useState('');

    const fetchAircraftModels = useCallback(async (currentPage, currentPerPage, currentSortField, currentSortOrder, currentSearchTerm) => {
        if (!isAuthenticated || !token) {
            setLoadingApi(false);
            return;
        }
        setLoadingApi(true);
        const orderingParam = `${currentSortOrder === "desc" ? "-" : ""}${currentSortField}`;
        let apiUrl = `/api/v1/envanter/aircraft-models/?page=${currentPage}&page_size=${currentPerPage}&ordering=${orderingParam}`;
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
            } else { setData([]); setTotalRows(0); }
            setApiError('');
        } catch (err) {
            console.error("Uçak modeli verileri çekilirken hata:", err);
            setData([]); setTotalRows(0); setApiError(err.message);
        } finally {
            setLoadingApi(false);
        }
    }, [token, isAuthenticated]);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchAircraftModels(page, perPage, sortField, sortOrder, searchTerm);
        }
    }, [page, perPage, sortField, sortOrder, searchTerm, fetchAircraftModels, authLoading, isAuthenticated]);

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
        { name: "Model Kodu (DB)", selector: row => row.name, sortable: true, sortField: "name" },
        { name: "Okunabilir Ad", selector: row => row.get_name_display, sortable: false },
        { name: "Oluşturulma", selector: row => row.created_at, sortable: true, sortField: "created_at", format: row => new Date(row.created_at).toLocaleDateString("tr-TR") },
    ], []); 

    if (authLoading) return <div className="p-6 text-center">Yükleniyor...</div>;
    
    return (
        <div className="container mx-auto p-4 xl:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                <h1 className="text-3xl font-semibold text-gray-700">Uçak Modelleri</h1>
                <input
                    type="text"
                    placeholder="Model adı ara..."
                    className="form-input px-4 py-2 border border-gray-300 rounded-md shadow-sm w-full sm:w-auto"
                    onChange={handleSearch}
                />
                {/* Yeni ekleme butonu olmayacak, çünkü data migration ile yönetiliyor */}
            </div>
            {apiError && <div className="alert-danger mb-4">{apiError}</div>}
            <div className="bg-white p-0 sm:p-2 rounded-xl shadow-xl overflow-x-auto">
                <DataTable
                    columns={columns}
                    data={data}
                    progressPending={loadingApi}
                    progressComponent={<div className="py-10 text-center text-gray-500">Uçak modelleri yükleniyor...</div>}
                    pagination
                    paginationServer
                    paginationTotalRows={totalRows}
                    onChangeRowsPerPage={handlePerRowsChange}
                    onChangePage={handlePageChange}
                    paginationResetDefaultPage={resetPaginationToggle}
                    sortServer
                    onSort={handleSort}
                    defaultSortFieldId={columns.findIndex(col => col.sortField === "name") + 1 || 1}
                    defaultSortAsc={true}
                    highlightOnHover
                    striped
                    responsive
                    noDataComponent={<div className="py-10 text-center text-gray-500">Gösterilecek uçak modeli bulunamadı.</div>}
                />
            </div>
        </div>
    );
}
export default AdminAircraftModelsPage;