/* =========================================================================
   Smart Parking — Admin dashboard (dashboard.html)
   Rendering + wiring against the real backend API (js/api.js).
   ========================================================================= */

async function renderStatCards(report, status) {
    const revenueEl = document.getElementById('stat-revenue');
    const servicedEl = document.getElementById('stat-serviced');

    if (report) {
        revenueEl.textContent = `Rs ${report.total_revenue.toFixed(2)}`;
        servicedEl.textContent = report.vehicles_serviced;
    } else {
        revenueEl.textContent = 'N/A';
        servicedEl.textContent = 'N/A';
    }

    document.getElementById('stat-parked').textContent = status.parked_count;
    document.getElementById('stat-waiting').textContent = status.waiting_count;
}

function renderSlotsTable(slots) {
    const tbody = document.getElementById('slots-table-body');
    if (!tbody) return;

    tbody.innerHTML = slots.map(s => {
        const badgeClass = s.status === 'Empty' ? 'status-empty'
            : s.status === 'Occupied' ? 'status-occupied' : 'status-outofservice';

        let actionButton = '<span class="empty-note">—</span>';
        if (s.status === 'Empty') {
            actionButton = `<button class="btn btn-outline-chalk btn-sm" data-action="disable" data-slot="${s.slot_number}">Mark Out of Service</button>`;
        } else if (s.status === 'OutOfService') {
            actionButton = `<button class="btn btn-outline-chalk btn-sm" data-action="enable" data-slot="${s.slot_number}">Mark Empty</button>`;
        }

        return `
            <tr>
                <td class="font-mono">${s.slot_number}</td>
                <td>${s.slot_type}</td>
                <td><span class="slot-badge ${badgeClass}">${s.status}</span></td>
                <td>${actionButton}</td>
            </tr>
        `;
    }).join('');

    tbody.querySelectorAll('button[data-action]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const slotNumber = btn.getAttribute('data-slot');
            const newStatus = btn.getAttribute('data-action') === 'disable' ? 'OutOfService' : 'Empty';
            const result = await setSlotStatus(slotNumber, newStatus);
            if (!result.ok) {
                alert(result.error || 'Could not update slot.');
            }
            await loadDashboard();
        });
    });
}

function renderHistoryTable(history) {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    if (history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-note text-center">No activity yet.</td></tr>';
        return;
    }

    tbody.innerHTML = history.map(h => `
        <tr>
            <td class="font-mono">${h.timestamp}</td>
            <td>${h.action_type}</td>
            <td class="font-mono">${h.vehicle_number}</td>
            <td class="font-mono">${h.slot_number}</td>
            <td>${h.amount ? `Rs ${h.amount.toFixed(2)}` : '—'}</td>
        </tr>
    `).join('');
}

function renderRevenueByType(report) {
    const el = document.getElementById('revenue-by-type');
    if (!el) return;

    if (!report || Object.keys(report.revenue_by_type).length === 0) {
        el.innerHTML = '<div class="empty-note">No completed transactions yet.</div>';
        return;
    }

    el.innerHTML = Object.entries(report.revenue_by_type).map(([type, amount]) => `
        <div class="list-row">
            <span>${type}</span>
            <span class="badge-type">Rs ${amount.toFixed(2)}</span>
        </div>
    `).join('');
}

function showConnectionError() {
    const banner = document.getElementById('connection-banner');
    if (banner) banner.classList.remove('d-none');
}

async function loadDashboard() {
    const [status, history, report] = await Promise.all([
        fetchStatus(),
        fetchHistory(50),
        fetchReport(),
    ]);
    renderStatCards(report, status);
    renderSlotsTable(status.slots);
    renderHistoryTable(history);
    renderRevenueByType(report);
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard().catch(showConnectionError);
});
