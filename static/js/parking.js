// ── Parking Grid – Slot Info Modal ─────────────────────────
function showSlotInfo(slot) {
  const modal    = document.getElementById('slotModal');
  const title    = document.getElementById('modal-title');
  const body     = document.getElementById('modal-body');
  const footer   = document.getElementById('modal-footer');

  title.textContent = `Slot ${slot.slot_number} – ${slot.slot_type.charAt(0).toUpperCase() + slot.slot_type.slice(1)}`;

  if (slot.is_occupied && slot.current_vehicle) {
    const v = slot.current_vehicle;
    body.innerHTML = `
      <div class="modal-info-row"><span>Status</span><strong><span class="badge badge-active">Occupied</span></strong></div>
      <div class="modal-info-row"><span>License Plate</span><strong><span class="plate-badge">${v.license_plate}</span></strong></div>
      <div class="modal-info-row"><span>Vehicle Type</span><strong>${capitalize(v.vehicle_type)}</strong></div>
      <div class="modal-info-row"><span>Owner</span><strong>${v.owner_name || '–'}</strong></div>
      <div class="modal-info-row"><span>Phone</span><strong>${v.phone || '–'}</strong></div>
      <div class="modal-info-row"><span>Entry Time</span><strong>${v.entry_time}</strong></div>
      <div class="modal-info-row"><span>Duration</span><strong>${v.duration_hours}h</strong></div>
      <div class="modal-info-row"><span>Est. Fee</span><strong style="color:var(--success)">₹${(v.duration_hours * 30).toFixed(2)}</strong></div>
    `;
    footer.innerHTML = `
      <a href="/exit" class="btn btn-danger btn-sm" id="modal-exit-btn">
        <i class="fas fa-sign-out-alt"></i> Process Exit
      </a>
      <button class="btn btn-secondary btn-sm" onclick="closeModal()" id="modal-close-btn">Close</button>
    `;
  } else {
    body.innerHTML = `
      <div class="modal-info-row"><span>Status</span><strong><span class="badge badge-active" style="background:rgba(16,185,129,0.15);color:var(--success)">Available</span></strong></div>
      <div class="modal-info-row"><span>Slot Type</span><strong>${capitalize(slot.slot_type)}</strong></div>
      <div class="modal-info-row"><span>Slot Number</span><strong>${slot.slot_number}</strong></div>
    `;
    footer.innerHTML = `
      <a href="/entry" class="btn btn-primary btn-sm" id="modal-book-btn">
        <i class="fas fa-car-side"></i> Park a Vehicle Here
      </a>
      <button class="btn btn-secondary btn-sm" onclick="closeModal()" id="modal-cancel-btn">Close</button>
    `;
  }

  modal.classList.add('open');
}

function closeModal() {
  document.getElementById('slotModal').classList.remove('open');
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});
