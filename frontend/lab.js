/**
 * AIEMCS - Lab Admin Panel JavaScript
 * Handles all admin panel interactions via fetch API.
 */

const API   = 'http://localhost:8000';
let   token = localStorage.getItem('aiemcs_token');
let   allEq = [];   // cached equipment for client-side filter

// ── Auth guard ────────────────────────────────────────────────────────────────

(function() {
  if (!token) { window.location.href = 'login.html'; return; }
  const user = JSON.parse(localStorage.getItem('aiemcs_user') || '{}');
  const label = document.getElementById('user-label');
  if (label && user.name) label.textContent = `👤 ${user.name}`;
})();

function logout() {
  localStorage.removeItem('aiemcs_token');
  localStorage.removeItem('aiemcs_user');
  window.location.href = 'login.html';
}

function authHeaders() {
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}


// ── Panel navigation ──────────────────────────────────────────────────────────

const PANELS = ['dashboard','equipment','add-equipment','timetable','schedule'];

function showPanel(name) {
  PANELS.forEach(p => document.getElementById(`panel-${p}`).classList.add('hidden'));
  document.getElementById(`panel-${name}`).classList.remove('hidden');
  document.querySelectorAll('.admin-sidebar a').forEach(a => a.classList.remove('active'));
  const match = [...document.querySelectorAll('.admin-sidebar a')].find(a => a.getAttribute('onclick')?.includes(name));
  if (match) match.classList.add('active');

  if (name === 'dashboard')  loadDashboard();
  if (name === 'equipment')  loadEquipment();
  if (name === 'schedule')   loadSchedule();
}


// ── Dashboard ─────────────────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const res = await fetch(`${API}/lab/equipment?limit=200`, { headers: authHeaders() });
    if (!res.ok) { handleAuthError(res); return; }
    const data = await res.json();

    const good  = data.filter(e => e.working_status === 'good').length;
    const fault = data.filter(e => e.working_status === 'faulty').length;
    const maint = data.filter(e => e.working_status === 'maintenance').length;

    document.getElementById('stat-total').textContent = data.length;
    document.getElementById('stat-good').textContent  = good;
    document.getElementById('stat-faulty').textContent = fault;
    document.getElementById('stat-maint').textContent  = maint;

    const tbody = document.getElementById('recent-tbody');
    tbody.innerHTML = data.slice(0, 10).map(e => `
      <tr>
        <td>${e.equipment_name}</td>
        <td>${e.equipment_category || '—'}</td>
        <td>${e.block_location || '—'}</td>
        <td><span class="badge badge-${e.working_status}">${e.working_status}</span></td>
      </tr>`).join('');
  } catch(err) {
    console.error(err);
  }
}


// ── Equipment list ────────────────────────────────────────────────────────────

async function loadEquipment() {
  const block  = document.getElementById('eq-block')?.value  || '';
  const status = document.getElementById('eq-status')?.value || '';

  let url = `${API}/lab/equipment?limit=200`;
  if (block)  url += `&block=${block}`;
  if (status) url += `&status_filter=${status}`;

  const loading = document.getElementById('eq-loading');
  if (loading) loading.textContent = 'Loading…';

  try {
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) { handleAuthError(res); return; }
    allEq = await res.json();
    renderEquipmentTable(allEq);
    if (loading) loading.textContent = '';
  } catch(err) {
    if (loading) loading.textContent = 'Failed to load. Is the server running?';
  }
}

function filterEquipment() {
  const q = (document.getElementById('eq-search')?.value || '').toLowerCase();
  const filtered = q ? allEq.filter(e => e.equipment_name.toLowerCase().includes(q)) : allEq;
  renderEquipmentTable(filtered);
}

function renderEquipmentTable(data) {
  const tbody = document.getElementById('eq-tbody');
  if (!tbody) return;
  tbody.innerHTML = data.map(e => `
    <tr>
      <td class="text-sm text-muted">${(e.tag||'').substring(0,24)}…</td>
      <td>${e.equipment_name}</td>
      <td>${e.equipment_category || '—'}</td>
      <td class="text-sm">${e.equipment_model_details ? e.equipment_model_details.substring(0,40)+'…' : '—'}</td>
      <td>${e.block_location || '—'}</td>
      <td>${e.quantity || 1}</td>
      <td><span class="badge badge-${e.working_status}">${e.working_status}</span></td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEdit(${e.id})">Edit</button>
        <button class="btn btn-danger btn-sm" onclick="deleteEquipment(${e.id}, this)">Del</button>
      </td>
    </tr>`).join('') || '<tr><td colspan="8" class="text-muted">No equipment found.</td></tr>';
}


// ── Add equipment ─────────────────────────────────────────────────────────────

document.getElementById('add-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn   = document.getElementById('add-btn');
  const alert = document.getElementById('add-alert');
  btn.disabled = true;
  btn.textContent = 'Saving…';

  const payload = {
    tag:                     document.getElementById('a-tag').value,
    equipment_name:          document.getElementById('a-name').value,
    equipment_category:      document.getElementById('a-cat').value,
    equipment_model_details: document.getElementById('a-spec').value,
    unit_price:              parseFloat(document.getElementById('a-price').value) || null,
    date_of_purchase:        document.getElementById('a-date').value || null,
    quantity:                parseInt(document.getElementById('a-qty').value) || 1,
    working_status:          document.getElementById('a-status').value,
    faculty:                 document.getElementById('a-faculty').value,
    deparment:               document.getElementById('a-dept').value,
    block_location:          document.getElementById('a-loc').value,
    source_id:               parseInt(document.getElementById('a-src').value) || null,
    incharge_id:             parseInt(document.getElementById('a-inc').value) || null,
  };

  try {
    const res = await fetch(`${API}/lab/equipment/add`, {
      method: 'POST', headers: authHeaders(), body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      showAlert('add-alert', 'error', data.detail || 'Failed to add equipment.');
    } else {
      showAlert('add-alert', 'success', `✅ Equipment "${data.equipment_name}" added (ID: ${data.id})`);
      document.getElementById('add-form').reset();
    }
  } catch(err) {
    showAlert('add-alert', 'error', 'Server error.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Add Equipment';
  }
});


// ── Edit modal ────────────────────────────────────────────────────────────────

function openEdit(id) {
  const eq = allEq.find(e => e.id === id);
  if (!eq) return;
  document.getElementById('edit-id').value     = id;
  document.getElementById('e-name').value      = eq.equipment_name;
  document.getElementById('e-cat').value       = eq.equipment_category || '';
  document.getElementById('e-loc').value       = eq.block_location || '';
  document.getElementById('e-qty').value       = eq.quantity || 1;
  document.getElementById('e-status').value    = eq.working_status || 'good';
  document.getElementById('e-spec').value      = eq.equipment_model_details || '';
  document.getElementById('edit-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('edit-modal').classList.add('hidden');
}

async function saveEdit() {
  const id = document.getElementById('edit-id').value;
  const payload = {
    equipment_name:          document.getElementById('e-name').value,
    equipment_category:      document.getElementById('e-cat').value,
    block_location:          document.getElementById('e-loc').value,
    quantity:                parseInt(document.getElementById('e-qty').value),
    working_status:          document.getElementById('e-status').value,
    equipment_model_details: document.getElementById('e-spec').value,
  };
  try {
    const res = await fetch(`${API}/lab/equipment/update/${id}`, {
      method: 'PUT', headers: authHeaders(), body: JSON.stringify(payload)
    });
    if (!res.ok) { alert('Update failed.'); return; }
    closeModal();
    loadEquipment();
  } catch(err) { alert('Server error.'); }
}

async function deleteEquipment(id, btn) {
  if (!confirm('Delete this equipment record?')) return;
  btn.disabled = true;
  try {
    const res = await fetch(`${API}/lab/equipment/${id}`, {
      method: 'DELETE', headers: authHeaders()
    });
    if (res.ok) {
      allEq = allEq.filter(e => e.id !== id);
      renderEquipmentTable(allEq);
    } else {
      alert('Delete failed.');
      btn.disabled = false;
    }
  } catch(err) { btn.disabled = false; }
}


// ── Timetable upload ──────────────────────────────────────────────────────────

function previewFile(input) {
  const preview = document.getElementById('file-preview');
  const name    = document.getElementById('file-name');
  if (input.files[0]) {
    name.textContent = input.files[0].name;
    preview.classList.remove('hidden');
  }
}

async function uploadTimetable() {
  const location = document.getElementById('tt-location').value.trim();
  const fileInput = document.getElementById('tt-file');
  const btn = document.getElementById('tt-btn');

  if (!location) { showAlert('tt-alert', 'error', 'Please enter a block location.'); return; }
  if (!fileInput.files[0]) { showAlert('tt-alert', 'error', 'Please select a file.'); return; }

  btn.disabled = true;
  btn.textContent = 'Processing…';
  document.getElementById('tt-result').classList.add('hidden');

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('location', location);

  try {
    const res = await fetch(`${API}/timetable/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },  // no Content-Type: let browser set boundary
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      showAlert('tt-alert', 'error', data.detail || 'Upload failed.');
    } else {
      showAlert('tt-alert', 'success', `✅ Processed ${data.saved} schedule entries from OCR.`);
      renderTimetableResult(data.entries);
    }
  } catch(err) {
    showAlert('tt-alert', 'error', 'Server error or OCR not available.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Process Timetable';
  }
}

function renderTimetableResult(entries) {
  const result = document.getElementById('tt-result');
  const tbody  = document.getElementById('tt-tbody');
  tbody.innerHTML = entries.map(e => `
    <tr>
      <td>${e.day || '—'}</td>
      <td>${e.slot || '—'}</td>
      <td>${e.activity || '—'}</td>
      <td>${e.room || '—'}</td>
    </tr>`).join('') || '<tr><td colspan="4" class="text-muted">No entries detected.</td></tr>';
  result.classList.remove('hidden');
}


// ── Schedule view ─────────────────────────────────────────────────────────────

async function loadSchedule() {
  const loc = document.getElementById('sch-location')?.value || '';
  const day = document.getElementById('sch-day')?.value || '';
  let url = `${API}/lab/schedule?`;
  if (loc) url += `block_location=${loc}&`;
  if (day) url += `day=${day}&`;

  try {
    const res = await fetch(url, { headers: authHeaders() });
    const data = await res.json();
    const tbody = document.getElementById('sch-tbody');
    tbody.innerHTML = data.map(e => `
      <tr>
        <td>${e.block_location}</td>
        <td>${e.type || '—'}</td>
        <td>${e.day || '—'}</td>
        <td>${e.slot || '—'}</td>
        <td><span class="badge badge-${e.activity==='free'?'free':'good'}">${e.activity || '—'}</span></td>
      </tr>`).join('') || '<tr><td colspan="5" class="text-muted">No schedule found.</td></tr>';
  } catch(err) {
    console.error(err);
  }
}


// ── Utilities ─────────────────────────────────────────────────────────────────

function showAlert(id, type, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `alert alert-${type === 'error' ? 'error' : 'success'}`;
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 5000);
}

function handleAuthError(res) {
  if (res.status === 401) {
    localStorage.removeItem('aiemcs_token');
    window.location.href = 'login.html';
  }
}

// Drag & drop upload
const dropZone = document.getElementById('drop-zone');
if (dropZone) {
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag');
    const files = e.dataTransfer.files;
    if (files[0]) {
      document.getElementById('tt-file').files = files;
      previewFile(document.getElementById('tt-file'));
    }
  });
}

// Init
showPanel('dashboard');
