// ── Clock ──────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
updateClock();
setInterval(updateClock, 1000);

// ── Sidebar Toggle ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('sidebarToggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const isMobile = window.innerWidth <= 768;
      if (isMobile) {
        document.body.classList.toggle('sidebar-open');
      } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', document.body.classList.contains('sidebar-collapsed'));
      }
    });
  }
  // Restore collapsed state
  if (localStorage.getItem('sidebar-collapsed') === 'true') {
    document.body.classList.add('sidebar-collapsed');
  }

  // Auto-dismiss flash messages after 5s
  const flashes = document.querySelectorAll('.alert');
  flashes.forEach(f => {
    setTimeout(() => {
      f.style.transition = 'opacity 0.4s';
      f.style.opacity = '0';
      setTimeout(() => f.remove(), 400);
    }, 5000);
  });
});

// ── Live Stats Refresh ──────────────────────────────────────
async function refreshStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const d = await res.json();

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('stat-available', d.available);
    set('stat-occupied',  d.occupied);
    set('stat-revenue',   '₹' + d.today_revenue);

    const fill = document.getElementById('occ-fill');
    const pct  = document.getElementById('occ-pct');
    if (fill) fill.style.width = d.occupancy_pct + '%';
    if (pct)  pct.textContent  = d.occupancy_pct + '%';
  } catch (_) {}
}
