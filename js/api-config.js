/* ABKNET API configuration
   After deploying the backend, replace the empty string with your API URL, e.g.
   https://abknet-technologies-api.onrender.com
*/
window.ABKNET_API_BASE = '';

window.abknetApi = function(path) {
  const base = (window.ABKNET_API_BASE || '').replace(/\/$/, '');
  return base + path;
};
