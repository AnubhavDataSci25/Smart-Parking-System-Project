/* =========================================================================
   Smart Parking — API client (Stage 4: real backend integration)

   This replaces the old localStorage-based demo logic. Every function
   here talks to the real Flask + PostgreSQL backend (backend/api.py) over
   fetch(). Because api.py serves this frontend as static files on the
   SAME origin, no CORS configuration is needed — this only works when
   the page is loaded via that server (e.g. http://localhost:5000), not
   by double-clicking index.html directly from disk.
   ========================================================================= */

const API_BASE = '';  // same-origin

async function apiRequest(path, options = {}) {
    const response = await fetch(API_BASE + path, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, status: response.status, data };
}

async function fetchStatus() {
    const { data } = await apiRequest('/api/status');
    return data; // { slots, parked, waiting, parked_count, waiting_count }
}

async function fetchHistory(limit = 20) {
    const { data } = await apiRequest(`/api/history?limit=${limit}`);
    return data; // array, most recent first
}

async function fetchReport() {
    const { ok, data } = await apiRequest('/api/report');
    return ok ? data : null;
}

async function vehicleEntry(vehicleNumber, ownerName, vehicleType) {
    const { data } = await apiRequest('/api/entry', {
        method: 'POST',
        body: JSON.stringify({ vehicle_number: vehicleNumber, owner_name: ownerName, vehicle_type: vehicleType }),
    });
    // data.status: "PARKED" | "QUEUED" | "ERROR"; data.error present on validation failure (400)
    if (data.error) return { status: 'ERROR', message: data.error };
    return {
        status: data.status,
        message: data.message,
        slot_number: data.slot_number,
        queue_position: data.queue_position,
    };
}

async function vehicleExit(vehicleNumber) {
    const { data } = await apiRequest('/api/exit', {
        method: 'POST',
        body: JSON.stringify({ vehicle_number: vehicleNumber }),
    });
    if (data.error) return { status: 'ERROR', message: data.error };
    return {
        status: data.status,
        message: data.message,
        amount: data.amount,
        slot_number: data.slot_freed_number,
        promoted: data.promoted_vehicle_number || null,
    };
}

async function searchVehicle(vehicleNumber) {
    const { ok, data } = await apiRequest(`/api/search/${encodeURIComponent(vehicleNumber)}`);
    if (!ok || !data.found) return null;
    return {
        vehicle_number: data.vehicle.vehicle_number,
        owner_name: data.vehicle.owner_name,
        vehicle_type: data.vehicle.vehicle_type,
        currently_parked: data.currently_parked,
        slot_number: data.slot_number,
        entry_time: data.entry_time,
    };
}

async function setSlotStatus(slotNumber, newStatus) {
    const { ok, data } = await apiRequest(`/api/slots/${encodeURIComponent(slotNumber)}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
    });
    return { ok, error: data.error || null };
}
