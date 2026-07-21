import axios from 'axios';

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 seconds timeout
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMessage = "Unknown Error Occurred";
    let errorType = "General Error";

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      errorMessage = "Request timed out. Please try again.";
      errorType = "Timeout";
    } else if (!error.response) {
      errorMessage = "Unable to connect to backend. Please check your network connection or ensure the backend server is running.";
      errorType = "Network Error";
    } else {
      const status = error.response.status;
      if (status === 404) {
        errorMessage = "The requested resource could not be found (404).";
        errorType = "Not Found";
      } else if (status >= 500) {
        errorMessage = "An internal server error occurred (500). Please try again later.";
        errorType = "Server Error";
      } else {
        errorMessage = error.response.data?.detail || error.response.data?.message || `HTTP Error ${status}`;
        errorType = "Error";
      }
    }

    return Promise.reject({ message: errorMessage, type: errorType, original: error });
  }
);

export default api;
