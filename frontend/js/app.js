/* =========================================================================
   Smart Parking — Attendant console (index.html)
   Rendering + form wiring against the real backend API (js/api.js).
   ========================================================================= */

async function renderAll() {
    const [status, history] = await Promise.all([fetchStatus(), fetchHistory(12)]);
    renderCounter(status.slots);
    renderSlotMap(status.slots);
    renderWaitingQueue(status.waiting);
    renderHistory(history);
}

function renderCounter(slots) {
    const empty = slots.filter(s => s.status === 'Empty').length;
    const el = document.getElementById('led-counter-value');
    if (el) el.textContent = `${empty} / ${slots.length} EMPTY`;
}

function renderSlotMap(slots) {
    const grid = document.getElementById('slot-grid');
    if (!grid) return;
    grid.innerHTML = '';
    slots.forEach(s => {
        const div = document.createElement('div');
        div.className = `slot status-${s.status.toLowerCase()}`;
        div.innerHTML = `${s.slot_number}<span class="type-tag">${s.slot_type}</span>`;
        grid.appendChild(div);
    });
}

function renderWaitingQueue(waiting) {
    const el = document.getElementById('waiting-list');
    if (!el) return;
    if (waiting.length === 0) {
        el.innerHTML = '<div class="empty-note">No one waiting right now.</div>';
        return;
    }
    el.innerHTML = waiting.map((w, i) => `
        <div class="list-row">
            <span>#${i + 1} ${w.vehicle_number}</span>
            <span class="badge-type">${w.vehicle_type}</span>
        </div>
    `).join('');
}

function renderHistory(history) {
    const el = document.getElementById('history-list');
    if (!el) return;
    if (history.length === 0) {
        el.innerHTML = '<div class="empty-note">No activity yet.</div>';
        return;
    }
    el.innerHTML = history.map(h => `
        <div class="list-row">
            <span>[${h.timestamp}] ${h.action_type} ${h.vehicle_number} @ ${h.slot_number}</span>
            ${h.amount ? `<span class="badge-type">Rs ${h.amount.toFixed(2)}</span>` : ''}
        </div>
    `).join('');
}

function renderTicket(containerId, { vehicleNumber, slotNumber, entryTime, exitTime, amount }) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = `
        <div class="ticket">
            <div class="ticket-header">SMART PARKING RECEIPT</div>
            <div class="ticket-row"><span>VEHICLE</span><span>${vehicleNumber}</span></div>
            <div class="ticket-row"><span>SLOT</span><span>${slotNumber}</span></div>
            <div class="ticket-row"><span>ENTRY</span><span>${entryTime || '-'}</span></div>
            <div class="ticket-row"><span>EXIT</span><span>${exitTime || '-'}</span></div>
            <div class="ticket-amount">Rs ${amount.toFixed(2)}</div>
            <div class="barcode"></div>
        </div>
    `;
    el.classList.remove('d-none');
}

function showConnectionError() {
    const banner = document.getElementById('connection-banner');
    if (banner) banner.classList.remove('d-none');
}

// ---------------------------------------------------------------------
// Wire up forms once the DOM is ready
// ---------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    renderAll().catch(showConnectionError);

    const entryForm = document.getElementById('entry-form');
    if (entryForm) {
        entryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const number = document.getElementById('entry-vehicle-number').value.trim().toUpperCase();
            const owner = document.getElementById('entry-owner-name').value.trim();
            const type = document.getElementById('entry-vehicle-type').value;
            if (!number || !owner) return;

            const result = await vehicleEntry(number, owner, type);
            document.getElementById('entry-feedback').textContent = result.message;
            await renderAll();
            if (result.status !== 'ERROR') entryForm.reset();
        });
    }

    const exitForm = document.getElementById('exit-form');
    if (exitForm) {
        exitForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const number = document.getElementById('exit-vehicle-number').value.trim().toUpperCase();
            if (!number) return;

            const result = await vehicleExit(number);
            const feedback = document.getElementById('exit-feedback');
            feedback.textContent = result.message + (result.promoted ? ` (Slot given to ${result.promoted} from the queue.)` : '');

            if (result.status === 'SUCCESS') {
                renderTicket('exit-ticket', {
                    vehicleNumber: number, slotNumber: result.slot_number,
                    entryTime: '-', exitTime: new Date().toLocaleString('en-IN', { hour12: false }),
                    amount: result.amount,
                });
                exitForm.reset();
            }
            await renderAll();
        });
    }

    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const number = document.getElementById('search-vehicle-number').value.trim().toUpperCase();
            const result = await searchVehicle(number);
            const el = document.getElementById('search-result');

            if (!result) {
                el.innerHTML = `<div class="empty-note">No vehicle found with number "${number}".</div>`;
                return;
            }
            const statusLine = result.currently_parked
                ? `Currently parked in slot ${result.slot_number} (since ${result.entry_time}).`
                : 'Not currently parked.';

            el.innerHTML = `
                <div class="list-row">
                    <span>${result.vehicle_number} — ${result.owner_name}</span>
                    <span class="badge-type">${result.vehicle_type}</span>
                </div>
                <div class="empty-note mt-2">${statusLine}</div>
            `;
        });
    }
});
