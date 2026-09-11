document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
    }
});

function pollQueue(callback, intervalMs) {
    async function tick() {
        try {
            const res = await fetch('/api/queue-today');
            if (!res.ok) return;
            const data = await res.json();
            callback(data);
        } catch (e) {}
    }
    tick();
    return setInterval(tick, intervalMs || 15000);
}
