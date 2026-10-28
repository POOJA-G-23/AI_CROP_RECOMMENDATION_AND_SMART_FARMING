// ─── auth.js — shared across all pages ───────────────────────────────────────
const Auth = {
  save(token, user) {
    localStorage.setItem("crop_token", token);
    localStorage.setItem("crop_user", JSON.stringify(user));
  },
  getToken() { return localStorage.getItem("crop_token"); },
  getUser()  { const u=localStorage.getItem("crop_user"); return u?JSON.parse(u):null; },
  isLoggedIn(){ return !!this.getToken(); },
  isAdmin()  { const u=this.getUser(); return u&&u.role==="admin"; },
  logout()   { localStorage.removeItem("crop_token"); localStorage.removeItem("crop_user"); window.location.href="/"; },

  // Attach token to every fetch
  async fetch(url, opts={}) {
    const token = this.getToken();
    opts.headers = opts.headers || {};
    if (token) opts.headers["Authorization"] = "Bearer " + token;
    opts.headers["Content-Type"] = opts.headers["Content-Type"] || "application/json";
    const resp = await fetch(url, opts);
    if (resp.status === 401) { this.logout(); return; }
    return resp;
  },

  // Guard — redirect to login if not authenticated
  guard(adminRequired=false) {
    if (!this.isLoggedIn()) { window.location.href="/"; return false; }
    if (adminRequired && !this.isAdmin()) { window.location.href="/app"; return false; }
    return true;
  },

  // Show user name in header
  renderHeader() {
    const u = this.getUser();
    const el = document.getElementById("userDisplay");
    if (el && u) el.innerHTML = `<span class="user-name"><i class="fa fa-user"></i> ${u.name}</span>`;
    const roleEl = document.getElementById("userRole");
    if (roleEl && u) { roleEl.innerText=u.role==="admin"?"Admin":"Farmer"; roleEl.className="role-badge role-"+u.role; }
  }
};

// Toast helper
function showToast(msg, type="info") {
  let t = document.getElementById("toast");
  if (!t) { t=document.createElement("div"); t.id="toast"; document.body.appendChild(t); }
  t.className = "toast toast-"+type;
  t.innerText = msg; t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"), 3000);
}
