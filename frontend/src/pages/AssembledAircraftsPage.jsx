import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import DataTable from 'react-data-table-component';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { deleteAssembledAircraftAPI } from '../api/aircraftService';

const customTableStyles = { /* Şimdilik Boş */ };
const paginationComponentOptions = { /* Şimdilik Boş */ };

/**
 * Monte edilmiş uçakları listeleyen, filtreleyen ve yöneten sayfa bileşeni.
 * Server-side data işlemleri için `react-data-table-component` kullanır.
 */
function AssembledAircraftsPage() {
    const { token, isAuthenticated, loading: authLoading, user } = useAuth();
    const navigate = useNavigate();

    const [data, setData] = useState([]);
    const [loadingApi, setLoadingApi] = useState(true);
    const [totalRows, setTotalRows] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage, setPerPage] = useState(10);
    const [sortField, setSortField] = useState("assembly_date"); // Varsayılan sıralama
    const [sortOrder, setSortOrder] = useState("desc");
    const [searchTerm, setSearchTerm] = useState('');
    const [resetPaginationToggle, setResetPaginationToggle] = useState(false);
    const [apiError, setApiError] = useState('');
    const dtRef = useRef(null);

    const fetchAssembledAircrafts = useCallback(async (currentPage, currentPerPage, currentSortField, currentSortOrder, currentSearchTerm) => {
        if (!isAuthenticated || !token) {
            setLoadingApi(false);
            return;
        }
        setLoadingApi(true);
        const orderingParam = `${currentSortOrder === "desc" ? "-" : ""}${currentSortField}`;
        let apiUrl = `/api/v1/montaj/assembled-aircrafts/?page=${currentPage}&page_size=${currentPerPage}&ordering=${orderingParam}`;
        if (currentSearchTerm) {
            apiUrl += `&search=${encodeURIComponent(currentSearchTerm)}`;
        }

        try {
            const res = await fetch(apiUrl, { headers: { Authorization: `Token ${token}` } });
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: "Bilinmeyen sunucu hatası" }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            const json = await res.json();
            if (json.results && typeof json.count !== 'undefined') {
                setData(json.results);
                setTotalRows(json.count);
            } else {
                setData([]);
                setTotalRows(0);
            }
        } catch (err) {
            console.error("Monte edilmiş uçak verileri çekilirken hata:", err);
            setData([]); setTotalRows(0); setApiError(err.message);
        } finally {
            setLoadingApi(false);
        }
    }, [token, isAuthenticated]);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchAssembledAircrafts(page, perPage, sortField, sortOrder, searchTerm);
        }
    }, [page, perPage, sortField, sortOrder, searchTerm, fetchAssembledAircrafts, authLoading, isAuthenticated]);

    const handlePageChange = useCallback(newPage => setPage(newPage), []);
    const handlePerRowsChange = useCallback((newPerPage, newPage) => {
        setPerPage(newPerPage);
        setPage(newPage);
    }, []);
    const handleSort = useCallback((column, sortDirection) => {
        if (column.sortField) {
            setSortField(column.sortField);
            setSortOrder(sortDirection);
            setPage(1);
        }
    }, []);
    const handleSearch = useCallback((event) => {
        setSearchTerm(event.target.value);
        setPage(1);
        setResetPaginationToggle(prev => !prev);
    }, []);

    const handleDeleteAircraft = async (aircraftId, tailNumber) => {
        if (window.confirm(`${tailNumber} kuyruk numaralı uçağı silmek istediğinize emin misiniz? Bu işlem, kullanılan parçaları stoğa döndürecektir.`)) {
            try {
                setLoadingApi(true);
                await deleteAssembledAircraftAPI(aircraftId); // API çağrısı
                alert("Uçak başarıyla silindi ve parçalar stoğa döndürüldü.");
                fetchAssembledAircrafts(page, perPage, sortField, sortOrder, searchTerm); // Tabloyu yenile
            } catch (err) {
                console.error("Uçak silme hatası:", err);
                setApiError(err.response?.data?.detail || err.response?.data?.error || "Uçak silinirken bir hata oluştu.");
            } finally {
                setLoadingApi(false);
            }
        }
    };

    const columns = useMemo(() => [
        { name: "ID", selector: row => row.id, sortable: true, sortField: "id", omit: true },
        { name: "Kuyruk No", selector: row => row.tail_number, sortable: true, sortField: "tail_number", wrap: true },
        { name: "Uçak Modeli", selector: row => row.aircraft_model_details?.name, sortable: true, sortField: "aircraft_model__name" }, 
        { name: "Montaj Tarihi", selector: row => row.assembly_date, sortable: true, sortField: "assembly_date", format: row => row.assembly_date ? new Date(row.assembly_date).toLocaleDateString("tr-TR") : "" },
        { name: "Montaj Takımı", selector: row => row.assembled_by_team_details?.get_name_display, sortable: false }, 
        { name: "Kanat S/N", selector: row => row.wing_details?.serial_number, sortable: false },
        // Diğer parça SN'leri eklenebilir
        {
            name: "İşlemler",
            button: true,
            cell: row => (
                <div className="flex items-center justify-center gap-x-1">
                    <button title="Detay" className="p-1 text-blue-600 hover:text-blue-800" onClick={() => navigate(`/assembled-aircrafts/${row.id}/view`)}>🔍</button>
                    
                    {user?.profile?.team_details?.get_name_display === 'Montaj Takımı' && (
                        <button title="Sil" className="p-1 text-red-600 hover:text-red-800" onClick={() => handleDeleteAircraft(row.id, row.tail_number)}>🗑️</button>
                    )}
                </div>
            )
        }
    ], [navigate, user]); // user eklendi

    if (authLoading) {
        return <div className="p-6 text-center text-gray-500">Kimlik bilgileri yükleniyor...</div>;
    }
    if (!isAuthenticated) {
        return <div className="p-6 text-center text-gray-500">Uçakları görüntülemek için lütfen giriş yapın.</div>;
    }
    // Sadece Montaj Takımı üyelerinin bu sayfayı görmesini sağlamak için ek kontrol
    if (user && user.profile?.team_details?.get_name_display !== 'Montaj Takımı') {
        return <div className="p-6 text-center text-red-500">Bu sayfaya erişim yetkiniz bulunmamaktadır.</div>;
    }

    return (
        <div className="container mx-auto p-4 xl:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                <h1 className="text-3xl font-semibold text-gray-700">Monte Edilmiş Uçaklar</h1>
                <div className="flex items-center gap-4 w-full sm:w-auto">
                     <input
                        type="text"
                        placeholder="Kuyruk no, model ara..."
                        className="form-input px-4 py-2 border border-gray-300 rounded-md shadow-sm w-full sm:w-64"
                        onChange={handleSearch}
                    />
                    {user?.profile?.team_details?.get_name_display === 'Montaj Takımı' && ( // Sadece Montaj Takımı yeni uçak monte edebilir
                        <Link
                            to="/assembled-aircrafts/new"
                            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow-md whitespace-nowrap"
                        >
                            + Yeni Uçak Monte Et
                        </Link>
                    )}
                </div>
            </div>

            {apiError && (
                <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 rounded" role="alert">
                    <p className="font-bold">Hata!</p>
                    <p>{apiError}</p>
                </div>
            )}

            <div className="bg-white p-0 sm:p-2 rounded-xl shadow-xl overflow-x-auto">
                <DataTable
                    columns={columns}
                    data={data}
                    progressPending={loadingApi}
                    progressComponent={<div className="py-10 text-center text-gray-500">Uçaklar yükleniyor...</div>}
                    pagination
                    paginationServer
                    paginationTotalRows={totalRows}
                    onChangeRowsPerPage={handlePerRowsChange}
                    onChangePage={handlePageChange}
                    paginationResetDefaultPage={resetPaginationToggle}
                    sortServer
                    onSort={handleSort}
                    defaultSortFieldId={columns.findIndex(col => col.sortField === "assembly_date") + 1 || 1}
                    defaultSortAsc={false}
                    highlightOnHover
                    striped
                    responsive
                    noDataComponent={<div className="py-10 text-center text-gray-500">Gösterilecek monte edilmiş uçak bulunamadı.</div>}
                    customStyles={customTableStyles}
                    paginationComponentOptions={paginationComponentOptions}
                />
            </div>
        </div>
    );
}

export default AssembledAircraftsPage;