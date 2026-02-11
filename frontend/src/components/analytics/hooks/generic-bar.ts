import api from '@/api';

type DataType = 'dividends' | 'investissements';

// Retourne les endpoints corrects selon le type
function getBasePath(dataType: DataType) {
  return `/api/portfolio/:id/performances/${dataType}`;
}

// Liste des années
export async function getAvailableYears(portfolioId: string, dataType: DataType) {
  const res = await api.get(
    getBasePath(dataType).replace(':id', portfolioId.toString()) + '/years-list/'
  );
  return res.data || [];
}

// Données mensuelles
export async function getMonthData(portfolioId: string, dataType: DataType) {
  const res = await api.get(
    getBasePath(dataType).replace(':id', portfolioId.toString()) + '/month/'
  );
  return res.data;
}

// Données mensuelles par ticker
export async function getMonthDataByTicker(portfolioId: string, dataType: DataType) {
  const res = await api.get(
    getBasePath(dataType).replace(':id', portfolioId.toString()) + '/month/by-ticker/'
  );
  return res.data;
}

// Données annuelles
export async function getYearData(portfolioId: string, dataType: DataType) {
  const res = await api.get(
    getBasePath(dataType).replace(':id', portfolioId.toString()) + '/year/'
  );
  return res.data;
}

// Données annuelles par ticker
export async function getYearDataByTicker(portfolioId: string, dataType: DataType) {
  const res = await api.get(
    getBasePath(dataType).replace(':id', portfolioId.toString()) + '/year/by-ticker/'
  );
  return res.data;
}
