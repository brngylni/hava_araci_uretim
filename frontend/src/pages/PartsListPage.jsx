import React, { useEffect, useState, useCallback, useMemo } from "react";
import DataTable from "react-data-table-component";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../api/axiosInstance";

const customTableStyles = {
    header: {
        style: {
            minHeight: '56px',
        },
    },
    headRow: {
        style: {
            borderTopStyle: 'solid',
            borderTopWidth: '1px',
            borderTopColor: 'rgb(229, 231, 235)', // tailwind gray-300
        },
    },
    headCells: {
        style: {
            '&:not(:last-of-type)': {
                borderRightStyle: 'solid',
                borderRightWidth: '1px',
                borderRightColor: 'rgb(229, 231, 235)',
            },
            fontSize: '0.875rem', // text-sm
            fontWeight: '600', // font-semibold
            color: 'rgb(55, 65, 81)', // text-gray-700
        },
    },
    cells: {
        style: {
            '&:not(:last-of-type)': {
                borderRightStyle: 'solid',
                borderRightWidth: '1px',
                borderRightColor: 'rgb(229, 231, 235)',
            },
            paddingLeft: '16px', // px-4
            paddingRight: '16px', // px-4
        },
    },
};

const paginationComponentOptions = {
    rowsPerPageText: 'Sayfa başına satır:',
    rangeSeparatorText: '/',
    selectAllRowsItem: true,
    selectAllRowsItemText: 'Tümü',
};


/**
 * Parça envanterini listeleyen, filtreleyen, sıralayan ve sayfalayan sayfa bileşeni.
 * Server-side data işlemleri için `react-data-table-component` kullanır.
 * Kullanıcıların yeni parça üretme, mevcut parçaları görüntüleme ve geri dönüşüme
 * gönderme gibi işlemleri yapmasına olanak tanır (API entegrasyonu TODO olarak işaretlenmiştir).
 */
function PartsListPage() {
    const { token, isAuthenticated, loading: authLoading, user } = useAuth();
    const navigate = useNavigate();

    const [data, setData] = useState([]);
    const [loadingApi, setLoadingApi] = useState(true); // API veri yükleme durumu
    const [totalRows, setTotalRows] = useState(0);
    const [page, setPage] = useState(1); // react-data-table-component 1 tabanlı sayfa kullanır
    const [perPage, setPerPage] = useState(10);
    const [sortField, setSortField] = useState("created_at"); // API'nin beklediği alan adı
    const [sortOrder, setSortOrder] = useState("desc");
    const [searchTerm, setSearchTerm] = useState(''); // Genel arama için
    const [resetPaginationToggle, setResetPaginationToggle] = useState(false); // Arama yapıldığında sayfalamayı resetlemek için


    const fetchParts = useCallback(async (currentPage, currentPerPage, currentSortField, currentSortOrder, currentSearchTerm) => {
        if (!isAuthenticated || !token) {
            setLoadingApi(false);
            return;
        }
        setLoadingApi(true);

        const orderingParam = `${currentSortOrder === "desc" ? "-" : ""}${currentSortField}`;
        let apiUrl = `/api/v1/envanter/parts/?page=${currentPage}&page_size=${currentPerPage}&ordering=${orderingParam}`;
        
        if (currentSearchTerm) {
            apiUrl += `&search=${encodeURIComponent(currentSearchTerm)}`;
        }
        
        try {
            const res = await fetch(apiUrl, {
                headers: { Authorization: `Token ${token}` }
            });
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: "Bilinmeyen sunucu hatası" }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            const json = await res.json();

            // Standart DRF PageNumberPagination yanıtı: {count, next, previous, results}
            if (json.results && typeof json.count !== 'undefined') {
                setData(json.results);
                setTotalRows(json.count);
            } else if (json.data && typeof json.recordsTotal !== 'undefined') {
                setData(json.data);
                setTotalRows(json.recordsTotal);
            }
            else {
                console.warn("Beklenmedik API yanıt formatı:", json);
                setData([]);
                setTotalRows(0);
            }
        } catch (err) {
            console.error("Parça verileri çekilirken hata oluştu:", err);
            setData([]);
            setTotalRows(0);
            // Kullanıcıya hata mesajı gösterilebilir (örneğin bir state ile)
        } finally {
            setLoadingApi(false);
        }
    }, [token, isAuthenticated]); 

    useEffect(() => {
        if (!authLoading && isAuthenticated) { // Sadece auth tamamlandıktan ve kullanıcı giriş yapmışsa
            fetchParts(page, perPage, sortField, sortOrder, searchTerm);
        }
    }, [page, perPage, sortField, sortOrder, searchTerm, fetchParts, authLoading, isAuthenticated]);


    const handlePageChange = useCallback(newPage => {
        setPage(newPage);
    }, []);

    const handlePerRowsChange = useCallback(async (newPerPage, newPage) => {
        setPerPage(newPerPage);
        setPage(newPage); // DataTable bu yeni sayfayı otomatik olarak iletir
    }, []);

    const handleSort = useCallback((column, sortDirection) => {
        // column.selector genellikle (row => row.fieldName) şeklindedir.
        // API'ye gönderilecek gerçek alan adını almak için column.sortField gibi bir property kullanmalıyız.
        if (column.sortField) {
            setSortField(column.sortField);
            setSortOrder(sortDirection);
            setPage(1); // Sıralama değiştiğinde ilk sayfaya dön
        } else {
            console.warn("Sortable column missing 'sortField' property:", column);
        }
    }, []);

    const handleSearch = useCallback((event) => {
        const newSearchTerm = event.target.value;
        setSearchTerm(newSearchTerm);
        setPage(1); // Arama yapıldığında ilk sayfaya dön
        setResetPaginationToggle(!resetPaginationToggle); // Sayfalamayı resetlemek için
    }, [resetPaginationToggle]);


    const columns = useMemo(() => [
        { name: "ID", selector: row => row.id, sortable: true, sortField: "id", omit: true /* ID'yi gizle ama sıralanabilir olsun */ },
        { name: "Seri No", selector: row => row.serial_number, sortable: true, sortField: "serial_number", wrap: true },
        { name: "Parça Tipi", selector: row => row.part_type_name, sortable: false /* veya backend'de part_type__name ile sırala */ },
        { name: "Uyumlu Model", selector: row => row.aircraft_model_compatibility_name, sortable: false /* veya backend'de ...__name ile sırala */ },
        { name: "Durum", selector: row => row.status_display, sortable: true, sortField: "status" },
        { name: "Üreten Takım", selector: row => row.produced_by_team_name, sortable: false /* veya backend'de ...__name ile sırala */ },
        {
            name: "Oluşturulma",
            selector: row => row.created_at,
            sortable: true,
            sortField: "created_at",
            format: row => row.created_at ? new Date(row.created_at).toLocaleDateString("tr-TR", { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ""
        },
        {
            name: "İşlemler",
            button: true,
            cell: row => (
                <div className="flex items-center justify-center gap-x-1">
                    <button
                        title="Detay"
                        className="p-1 text-blue-600 hover:text-blue-800"
                        onClick={() => navigate(`/parts/${row.id}/view`)} 
                    >
                    </button>
                    {row.produced_by_team_name == user.profile?.team_details?.get_name_display &&
                    <button
                        title="Geri Dönüştür"
                        className="p-1 text-yellow-600 hover:text-yellow-800"
                        onClick={async () => {
                            if (window.confirm(`${row.serial_number} S/N'li parçayı geri dönüşüme göndermek istediğinize emin misiniz?`)) {
                                try {
                                    setLoadingApi(true);
                                    await axiosInstance.post(`/api/v1/envanter/parts/${row.id}/recycle/`);
                                    alert("Parça başarıyla geri dönüşüme gönderildi.");
                                    fetchParts(page, perPage, sortField, sortOrder, searchTerm); // Tabloyu yenile
                                } catch (err) {
                                    console.error("Geri dönüşüm hatası:", err);
                                    alert(err.response?.data?.error || err.response?.data?.detail || "Geri dönüşüm sırasında bir hata oluştu.");
                                    setLoadingApi(false);
                                }
                            }
                        }}
                    >
                    </button>}
                </div>
            )
        }
    ], [navigate, page, perPage, sortField, sortOrder, searchTerm, fetchParts]); // fetchParts'ı bağımlılıklara ekle

    if (authLoading) {
        return <div className="p-6 text-center text-gray-500">Kimlik bilgileri yükleniyor...</div>;
    }
    if (!isAuthenticated) {
        return <div className="p-6 text-center text-gray-500">Parçaları görüntülemek için lütfen giriş yapın.</div>;
    }

    return (
        <div className="container mx-auto p-4 xl:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                <h1 className="text-3xl font-semibold text-gray-700">Parça Envanteri</h1>
                <div className="flex items-center gap-4 w-full sm:w-auto">
                    <input
                        type="text"
                        placeholder="Seri no, tip, model ara..."
                        className="form-input px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 w-full sm:w-64"
                        onChange={handleSearch} 
                    />
                    <button
                        onClick={() => navigate("/parts/new")} 
                        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded shadow-md hover:shadow-lg transition duration-150 ease-in-out whitespace-nowrap"
                    >
                        + Yeni Parça Üret
                    </button>
                </div>
            </div>

            <div className="bg-white p-0 sm:p-2 rounded-xl shadow-xl overflow-x-auto">
                <DataTable
                    columns={columns}
                    data={data}
                    progressPending={loadingApi}
                    progressComponent={<div className="py-10 text-center text-gray-500">Parçalar yükleniyor...</div>}
                    
                    pagination
                    paginationServer
                    paginationTotalRows={totalRows}
                    onChangeRowsPerPage={handlePerRowsChange}
                    onChangePage={handlePageChange}
                    paginationResetDefaultPage={resetPaginationToggle} // Arama yapıldığında sayfalamayı resetler
                    
                    sortServer
                    onSort={handleSort}
                    defaultSortFieldId={columns.findIndex(col => col.sortField === "created_at") + 1 || 1} 
                    defaultSortAsc={false}

                    highlightOnHover
                    striped
                    responsive
                    noDataComponent={<div className="py-10 text-center text-gray-500">Gösterilecek parça bulunamadı.</div>}
                    customStyles={customTableStyles} 
                    paginationComponentOptions={paginationComponentOptions} 
                />
            </div>
        </div>
    );
}

export default PartsListPage;