export const getApiData = (response) => response?.data?.data ?? response?.data;

export const getApiList = (response) => {
  const data = response?.data?.data ?? response?.data;
  return Array.isArray(data) ? data : [];
};

export const getApiExtra = (response) => response?.data?.extra || null;

export const getApiErrorMessage = (err, fallback = 'Something went wrong') => {
  const data = err?.response?.data;
  return data?.detail || data?.message || data?.error || fallback;
};
