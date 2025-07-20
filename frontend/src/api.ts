import axios from 'axios';

const baseURL = import.meta.env.VITE_BACKEND_URL;
console.log('API baseURL:', baseURL);

const api = axios.create({
  baseURL,
});

export default api; 