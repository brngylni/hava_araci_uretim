import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import DataTable from 'react-data-table-component';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { deletePartTypeAPI } from '../../api/partTypeService';

function AdminPartTypesPage() {
    const { token, isAuthenticated, loading: authLoading } = useAuth();
    const navigate = useNavigate();

    const [data, setData] = useState([]);
    const [loadingApi, setLoadingApi] = useState(true);
    const [totalRows, setTotalRows] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage, setPerPage] = useState(10);
    const [sortField, setSortField] = useState("name"); 
    const [sortOrder, setSortOrder] = useState("asc");
    const [apiError, setApiError] = useState('');
    const dtRef = useRef(null);

    const fetchPartTypes = useCallback(async (currentPage, currentPerPage, currentSortField, currentSortOrder) => {
        if (!isAuthenticated || !token) {
            setLoadingApi(false);
            return;
        }
        setLoadingApi(true);
        const orderingParam = `${currentSortOrder === "desc" ? "-" : ""}${currentSortField}`;
        let apiUrl = `/api/v1/envanter/part-types/?page=${currentPage}&page_size=${currentPerPage}&ordering=${orderingParam}`;
        
        try {
            const res = await fetch(apiUrl, { headers: { Authorization: `Token ${token}` } });
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            const json = await res.json();
            
            if (json.results && typeof json.count !== 'undefined') {
                setData(json.results);
                setTotalRows(json.count);
            } else if (json.data && typeof json.recordsTotal !== 'undefined') { // DRF-Datatables
                setData(json.data);
                setTotalRows(json.recordsTotal);
            } else { setData([]); setTotalRows(0); }
            setApiError('');
        } catch (err) {
            console.error("Parça tipi verileri çekilirken hata:", err);
            setData([]); setTotalRows(0); setApiError(err.message);
        } finally {
            setLoadingApi(false);
        }
    }, [token, isAuthenticated]);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchPartTypes(page, perPage, sortField, sortOrder);
        }
    }, [page, perPage, sortField, sortOrder, fetchPartTypes, authLoading, isAuthenticated]);

    const handlePageChange = useCallback(newPage => setPage(newPage), []);
    const handlePerRowsChange = useCallback((newPerPage, newPage) => {
        setPerPage(newPerPage); setPage(newPage);
    }, []);
    const handleSort = useCallback((column, sortDirection) => {
        if (column.sortField) {
            setSortField(column.sortField); setSortOrder(sortDirection); setPage(1);
        }
    }, []);

    const handleDelete = async (id, name) => {
        if (window.confirm(`'${name}' parça tipini silmek istediğinize emin misiniz? Bu tipte parçalar varsa silme işlemi başarısız olabilir.`)) {
            try {
                setLoadingApi(true);
                await deletePartTypeAPI(id);
                alert("Parça tipi başarıyla silindi.");
                fetchPartTypes(page, perPage, sortField, sortOrder); // Listeyi yenile
            } catch (err) {
                console.error("Parça tipi silme hatası:", err);
                setApiError(err.response?.data?.error || err.response?.data?.detail || "Silme işlemi başarısız oldu.");
            } finally {
                setLoadingApi(false);
            }
        }
    };

    const columns = useMemo(() => [
        { name: "ID", selector: row => row.id, sortable: true, sortField: "id", omit: true },
        { name: "Kod Adı (DB)", selector: row => row.name, sortable: true, sortField: "name" },
        { name: "Okunabilir Ad", selector: row => row.get_name_display, sortable: false }, // get_name_display backend'den gelmeli
        { name: "Oluşturulma", selector: row => row.created_at, sortable: true, sortField: "created_at", format: row => new Date(row.created_at).toLocaleDateString("tr-TR") },
       
    ], [fetchPartTypes, page, perPage, sortField, sortOrder]); 

    if (authLoading) return <div className="p-6 text-center">Yükleniyor...</div>;

    return (
        <div className="container mx-auto p-4 xl:p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-semibold text-gray-700">Parça Tipi Yönetimi</h1>
            </div>
            {apiError && <div className="alert-danger mb-4">{apiError}</div>}
            <div className="bg-white p-0 sm:p-2 rounded-xl shadow-xl overflow-x-auto">
                <DataTable
                    columns={columns}
                    data={data}
                    progressPending={loadingApi}
                    pagination
                    paginationServer
                    paginationTotalRows={totalRows}
                    onChangeRowsPerPage={handlePerRowsChange}
                    onChangePage={handlePageChange}
                    sortServer
                    onSort={handleSort}
                    defaultSortFieldId={columns.findIndex(col => col.sortField === "name") + 1 || 1} // name'e göre sırala
                    highlightOnHover
                    striped
                    responsive
                    noDataComponent={<div className="py-10 text-center text-gray-500">Gösterilecek parça tipi bulunamadı.</div>}
                />
            </div>
        </div>
    );
}
export default AdminPartTypesPage;